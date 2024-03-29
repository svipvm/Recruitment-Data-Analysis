from sentence_transformers import SentenceTransformer, util
import cpca, re, json, torch, pickle, os, hashlib
import numpy as np
import pandas as pd

DEBUG = False

require_edu_re_json = {'不限': 0, '技工': 1, '大专': 2, '本科': 3, '硕士': 4, '博士': 5}
level_json = {'COMMONLY': 1, 'GOOD': 2, 'SKILLED': 3, 'MASTER': 4}

equal_field_dict = {} # field_key {sentence: ..., vector: ...}

JOB_CSV_FILE = 'datasets/recruitment-info.csv'
HUNTER_CSV_FILE = 'datasets/hunter-info.csv'

os.makedirs('database', exist_ok=True)
def _read_database(data_file, json_type=True):
    try:
        if json_type:
            with open(data_file + '.json', 'r', encoding='GBK') as f:
                info_bak = json.loads(f.read())
        else:
            with open(data_file + '.data', 'rb') as f:
                info_bak = pickle.load(f)
        if DEBUG: print(data_file, 'size:', len(info_bak))
        return info_bak
    except Exception as e:
        if DEBUG: print(data_file, 'lost, record again!')
        return {}


def _save_database(data_file, data_dict, json_type=True):
    if json_type:
        with open(data_file + '.json', 'w', encoding='GBK') as f:
            f.write(json.dumps(data_dict, cls=NpEncoder))
    else:
         with open(data_file + '.data', 'wb') as f:
            pickle.dump(data_dict, f)

BASE_JOB_INFO_BAK_FILE = 'database/base_job_info'
base_job_info_bak = _read_database(BASE_JOB_INFO_BAK_FILE, DEBUG)

BASE_HUNTER_INFO_BAK_FILE = 'database/base_hunter_info'
base_hunter_info_bak = _read_database(BASE_HUNTER_INFO_BAK_FILE, DEBUG)

MAIN_JOB_INFO_BAK_FILE = 'database/main_job_info'
main_job_info_bak = _read_database(MAIN_JOB_INFO_BAK_FILE, DEBUG)

MAIN_HUNTER_INFO_BAK_FILE = 'database/main_hunter_info'
main_hunter_info_bak = _read_database(MAIN_HUNTER_INFO_BAK_FILE, DEBUG)

EXTRA_JOB_INFO_BAK_FILE = 'database/extra_job_info'
extra_job_info_bak = _read_database(EXTRA_JOB_INFO_BAK_FILE, DEBUG)

EXTRA_HUNTER_INFO_BAK_FILE = 'database/extra_hunter_info'
extra_hunter_info_bak = {}
extra_hunter_info_bak = _read_database(EXTRA_HUNTER_INFO_BAK_FILE, DEBUG)

BOTH_INFO_MAP_BAK_FILE = 'database/both_info_map'
both_info_map_bak = _read_database(BOTH_INFO_MAP_BAK_FILE, DEBUG)

_max_index_for_both_info = [-1, -1]

BOTH_SCORE_INFO_BAK_FILE = 'database/both_score_info'
both_score_info_bak = _read_database(BOTH_SCORE_INFO_BAK_FILE, DEBUG)

modified_obj = {}

BASE_MODEL_PATH = 'models/model_zoo/medium'

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def get_model(data_name):
    '''
    Args:
        - data_name: One of them base, main and extra
    Returns: result model example
    '''
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    if data_name == 'base' or data_name == 'extra':
        return SentenceTransformer(BASE_MODEL_PATH, device=device)
    elif data_name == 'main':
        return SentenceTransformer(BASE_MODEL_PATH, device=device)
    else:
        return None
    

def _get_both_data():
    '''
    Returns: result job and hunter data
    '''
    job_data = pd.read_csv(JOB_CSV_FILE, encoding='GBK')
    hunter_data = pd.read_csv(HUNTER_CSV_FILE, encoding='GBK')
    return job_data, hunter_data

job_data, hunter_data = _get_both_data()

def try_to_eval(item):
    '''
    Try to convert item to a list

    Args:
        - item: A item will be convert
    Returns: The converted list
    '''
    try:
        items = eval(item)
        return [str(item) for item in items]
    except:
        return [str(item)]
    
def multi_index_to_one(item_list):
    '''
    Multiple objects are converted into a list

    Args:
        - item_list: Multiple objects to store
    Returns: The converted list
    '''
    if not isinstance(item_list, list):
        return [str(item_list)]
    result = None
    for item in item_list:
        if not result: result = try_to_eval(item) 
        else: result += try_to_eval(item)
    return result

def change_wage(min_wage, max_wage, wage_kind=1):
    '''
    Transfer salary to monthly salary

    Args:
        - min_wage: Minimum wage for a specified salary type
        - max_wage: Maximum wage for a specified salary type
        - wage_kind: A salary type. 2 is the daily wage, 1 is the monthly salary, and 0 is the annual salary
    Returns: A monthly salary
    '''
    return [min_wage // 12, max_wage // 12] if wage_kind == 0 \
        else ([min_wage * 30, max_wage * 30] if wage_kind == 2 else [min_wage, max_wage])

def change_addrs(addrs):
    '''
    Extract the address from the text list

    Args: 
        - addrs: A text list containing address information
    Returns: Contains the address of the province or city
    '''
    if not isinstance(addrs, list): addrs = [addrs]
    province, city = None, None
    # print(addrs)
    for addr in addrs:
        addr = cpca.transform([addr])
        if not province and addr['省'][0]: province = addr['省'][0] 
        if not city and addr['市'][0]: city = addr['市'][0] 
        # print(province, city)
    return (str(province) + str(city)).replace('None', '').replace('市县', '市')

def change_edus(edus):
    '''
    Extract qualifications from educational experience

    Args: 
        - edus: A test list containing educational experience
    Returns: Educational list
    '''
    return [re.findall(r'\[(.*)\]', edu)[0] for edu in edus]

def delete_same_elem(list_like):
    '''
    Remove the same element from the list

    Args: 
        - list_like: The list to deweight
    Returns: List after deweighting
    '''
    return np.unique(np.array(list_like)).tolist()

def change_years(years):
    '''
    Extract the number of years from text information containing the year

    Args:
        - years: a test list containing the year
    Returns:  List containg the number of years
    '''
    years = re.findall(r'(\d+)', years)
    years = [int(year) for year in years]
    if len(years) == 0: years = [0]
    return years

def every_multi_score(vector1, vector2, method='mean', weights=None):
    '''
    The influence of vector2 on it is measured from the perspective of vector1

    Args:
        - vector1: Main vector
        - vector2: Vice vector
        - method: The type of the influence
    Returns: A score of the degree of impact
    '''
    if not isinstance(vector1, torch.Tensor): vector1 = torch.tensor(vector1)
    if not isinstance(vector2, torch.Tensor): vector2 = torch.tensor(vector2)
    # print(vector1.shape, vector2.shape)
    cos_score = util.cos_sim(vector1, vector2).numpy()
    # scores = [np.max(cos_score[i, :], keepdims=False) for i in range(cos_score.shape[0])]
    scores = np.max(cos_score, axis=1)
    if method == 'mean':
        multi_score = np.mean(scores)
    elif method == 'max':
        multi_score = np.max(scores)
    elif method == 'k-mean':
        k_rate = int(np.ceil(len(scores) * 0.6))
        multi_score = np.mean(np.sort(scores)[-k_rate:])
    elif method == 'weights':
        weights = np.array(weights)
        max_indexs = np.argmax(cos_score, axis=1)
        # print(scores, max_indexs, weights)
        multi_score = np.mean(scores * weights[max_indexs])
    else: # sum
        multi_score = np.dot(scores, [1] * len(scores))
    return multi_score

def get_max_edu_level(sentence, level_json):
    '''
    Extract the largest degree level from the degree list

    Args:
        - sentence: A degree list
        - level_json: Mapping from education to level
    Returns: Maximum degree grade
    '''
    if len(sentence) == 0: return 0
    level = [level_json[edu] for edu in sentence]
    return np.max(level, keepdims=False)

def show_base_info(base_dict, index):
    '''
    Outputs the body information of an object

    Args:
        - base_dict: Main information map
        - index: Index of the output information
    Returns: Returns information that does not contain the primary key
    '''
    return '。'.join([str(value['sentence']) for _, value in base_dict[list(base_dict.keys())[index]].items()])

def _dict_object_encode(info_id, info_dict: dict):
    '''
    Outputs the all information of an object

    Args:
        - info_id: A id of a object
        - info_dict: Content information map
    Returns: Returns information that contain the primary key
    '''
    # return '-'.join(["PREFIX" + info_id] + [str(value['sentence']) for _, value in info_dict.items()])
    return hashlib.sha256('-'.join(["PREFIX" + info_id] + [str(value['sentence']) for _, value in info_dict.items()]
                           ).encode('utf8')).hexdigest()

def _record_is_modified(obj_type, obj_id):
    '''
    Records the modified object key

    Args:
        - obj_type: The type of object in which the information is being recorded
        - obj_id: The id of the object of the corresponding type
    Returns: None
    '''
    if obj_type not in modified_obj:
        modified_obj[obj_type] = []
    modified_obj[obj_type].append(obj_id)

def info_is_modified(obj_type, obj_id):
    '''
    Determines whether the object has been modified

    Args:
        - obj_type: The type of object
        - obj_id: The id of the object
    Returns: Modified is true, otherwise false
    '''
    # print(modified_obj)
    if obj_type not in modified_obj: return False
    return obj_id in modified_obj[obj_type]

def is_modified_info_item(data_name, obj_type, info_id, info_dict):
    '''
    Update the information if it has been modified

    Args:
        - obj_type: The type of object
        - info_id: The id of the object
        - info_dict: The information of the object
    Returns: Modified is false, otherwise true
    '''
    if data_name == 'base':
        info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    elif data_name == 'main':
        info_bak = main_job_info_bak if obj_type == 0 else main_hunter_info_bak
    elif data_name == 'extra':
        info_bak = extra_job_info_bak if obj_type == 0 else extra_hunter_info_bak

    if info_id not in info_bak:
        _record_is_modified(obj_type, info_id)
        # print(1, info_id)
        return True
    else:
        item_value = _dict_object_encode(info_id, info_dict)
        item_bak_value = _dict_object_encode(info_id, info_bak[info_id])
        modified = (item_bak_value != item_value)
        if modified: _record_is_modified(obj_type, info_id)
        # print(0, info_id, )
        return modified

def get_info_item(data_name, obj_type, info_id):
    '''
    Get object information from the backup system

    Args:
        - obj_type: The type of object
        - info_id: The id of the object
    Returns: The object information recorded in the backup system
    '''
    # info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    if data_name == 'base':
        info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    elif data_name == 'main':
        info_bak = main_job_info_bak if obj_type == 0 else main_hunter_info_bak
    elif data_name == 'extra':
        info_bak = extra_job_info_bak if obj_type == 0 else extra_hunter_info_bak
    # print(len(info_bak))
    assert info_id in info_bak
    return info_bak[info_id]

def set_info_item(data_name, obj_type, info_id, info_data):
    '''
    Set object information from the backup system

    Args:
        - obj_type: The type of object
        - info_id: The id of the object
    Returns: The object information recorded in the backup system
    '''
    # info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    if data_name == 'base':
        info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    elif data_name == 'main':
        info_bak = main_job_info_bak if obj_type == 0 else main_hunter_info_bak
    elif data_name == 'extra':
        info_bak = extra_job_info_bak if obj_type == 0 else extra_hunter_info_bak
    # print(len(info_bak))
    # assert info_id in info_bak
    info_bak[info_id] = info_data

def save_info_database(data_name, obj_type, data_dict):
    '''
    Update object information in the backup system

    Args:
        - obj_type: The type of object
        - data_dict: Information about the object to save
    Returns: None
    '''
    # global base_job_info_bak, base_hunter_info_bak
    # global main_job_info_bak, main_hunter_info_bak
    # global extra_job_info_bak, extra_hunter_info_bak

    if data_name == 'base':
        info_bak_file = BASE_JOB_INFO_BAK_FILE if obj_type == 0 else BASE_HUNTER_INFO_BAK_FILE
        # if obj_type == 0: base_job_info_bak = data_dict
        # else: base_hunter_info_bak = data_dict
        # info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    elif data_name == 'main':
        info_bak_file = MAIN_JOB_INFO_BAK_FILE if obj_type == 0 else MAIN_HUNTER_INFO_BAK_FILE
        # info_bak = main_job_info_bak if obj_type == 0 else main_hunter_info_bak
        # if obj_type == 0: main_job_info_bak = data_dict
        # else: main_hunter_info_bak = data_dict
    elif data_name == 'extra':
        info_bak_file = EXTRA_JOB_INFO_BAK_FILE if obj_type == 0 else EXTRA_HUNTER_INFO_BAK_FILE
        # info_bak = extra_job_info_bak if obj_type == 0 else extra_hunter_info_bak
        # if obj_type == 0: extra_job_info_bak = data_dict
        # else: extra_hunter_info_bak = data_dict
    elif data_name == 'equal':
        info_bak_file = 'database/equal_field_info'
        # info_bak = None
    # print(type(data_dict))
    # with open(info_bak_file, 'w') as f:
    #     f.write(json.dumps(data_dict, cls=NpEncoder))
    _save_database(info_bak_file, data_dict, DEBUG)
    # info_bak = data_dict

def get_index_by_object_id(obj_type, obj_id):
    '''
    Gets the index of the object key from the backup system

    Args:
        - obj_type: The type of object
        - obj_id: The id(key) of object
    Returns: Returns the corresponding index if the object exists, otherwise -1
    '''
    obj_name = 'jobs' if obj_type == 0 else 'hunters'
    if obj_id in both_info_map_bak[obj_name]:
        return both_info_map_bak[obj_name][obj_id]
    else:
        return -1
    
def set_index_by_object_id(obj_type, obj_id):
    '''
    Objects that are not in the backup system index information added to the backup system

    Args:
        - obj_type: The type of object
        - obj_id: The id of object
    Returns: None
    '''
    obj_name = 'jobs' if obj_type == 0 else 'hunters'
    if obj_name not in both_info_map_bak:
        both_info_map_bak[obj_name] = {}
    if obj_id not in both_info_map_bak[obj_name]:
        both_info_map_bak[obj_name][obj_id] = len(both_info_map_bak[obj_name])
    _max_index_for_both_info[obj_type] = max(_max_index_for_both_info[obj_type], 
                                                len(both_info_map_bak[obj_name]))

def _get_max_index_for_both_info():
    '''
    Returns the maximum number of indexes for both classes of objects

    Returns: Maximum number of indexes for both categories
    '''
    return _max_index_for_both_info

def _expand_score_database_by_obj_type(obj_type):
    '''
    Extend the number of information in the relational matrix.
    Extend the main index (x) and vice index (y), which are relative to obj_type

    Args:
        - obj_type: The type of object
    Returns: None
    '''
    num_job, num_hunter = _get_max_index_for_both_info()
    max_inx, max_iny = (num_job, num_hunter) if obj_type == 0 else (num_hunter, num_job)
    obj_name = 'jobs' if obj_type == 0 else 'hunters'
    if obj_name not in both_score_info_bak:
        both_score_info_bak[obj_name] = [[]]
    if not isinstance(both_score_info_bak[obj_name], np.ndarray):
        both_score_info_bak[obj_name] = np.array(both_score_info_bak[obj_name], np.float16)
    if both_score_info_bak[obj_name].shape[1] == 0:
        both_score_info_bak[obj_name] = np.array([[[-1.0] * 3] * max_iny] * max_inx)
    else:
        num_inx, num_iny = both_score_info_bak[obj_name].shape[:2]
        # print(max_inx, num_inx, max_iny, num_iny)
        # expend for col
        if max_iny != num_iny:
            both_score_info_bak[obj_name] = np.column_stack((
                both_score_info_bak[obj_name],
                np.array([[[-1.0] * 3] * (max_iny - num_iny)] * num_inx)
            ))
        # expend for row
        if max_inx != num_inx:
            both_score_info_bak[obj_name] = np.row_stack((
                both_score_info_bak[obj_name],
                np.array([[[-1.0] * 3] * max_iny] * (max_inx - num_inx))
            ))

def expand_score_database():
    '''
    Extend the data for both types of objects separately
    '''
    _expand_score_database_by_obj_type(0)
    _expand_score_database_by_obj_type(1)

def set_score_by_multi_id(obj_type, row_key, col_key, score_id, score):
    '''
    Update the score information in the backup system

    Args:
        - obj_type: The type of main object
        - row_key: The key of main object
        - col_key: The key of vice object
        - score_id: The type of object
        - score: The score to store
    Returns: None
    '''
    obj_name = 'jobs' if obj_type == 0 else 'hunters'
    row_id = get_index_by_object_id(obj_type, row_key)
    col_id = get_index_by_object_id(obj_type ^ 1, col_key)
    # print(row_id, col_id, score_id, score)
    if row_id != -1 and col_id != -1:
        both_score_info_bak[obj_name][row_id][col_id][score_id] = score
    else:
        print(row_id, col_id)

def get_score_by_multi_id(obj_type, row_key, col_key, score_id):
    '''
    Gets the object score from the backup system

    Args:
        - obj_type: The type of main object
        - row_key: The key of main object
        - col_key: The key of vice object
        - score_id: The type of object
    Returns: Scores in the corresponding backup system
    '''
    obj_name = 'jobs' if obj_type == 0 else 'hunters'
    row_id = get_index_by_object_id(obj_type, row_key)
    col_id = get_index_by_object_id(obj_type ^ 1, col_key)
    if row_id != -1 and col_id != -1:
        return both_score_info_bak[obj_name][row_id][col_id][score_id]
    else:
        print(row_id, col_id)

def save_both_info_map_database():
    '''
    Update object index information in the backup system
    '''
    # with open(BOTH_INFO_MAP_BAK_FILE, 'w') as f:
    #     f.write(json.dumps(both_info_map_bak, cls=NpEncoder))
    _save_database(BOTH_INFO_MAP_BAK_FILE, both_info_map_bak, DEBUG)

def save_both_score_info_database():
    '''
    Update object score information in the backup system
    '''
    # with open(BOTH_SCORE_INFO_BAK_FILE, 'w') as f:
    #     f.write(json.dumps(both_score_info_bak, cls=NpEncoder))
    _save_database(BOTH_SCORE_INFO_BAK_FILE, both_score_info_bak, DEBUG)

def parse_long_text_list(text_list):
    '''
    Removes a specific model from the text list

    Args:
        - text_list: The text list for remove model
    '''
    WORD_THRESHOLD = 10
    pre_delete_patterns = [r'【\w*】']
    split_patterns = [r'\d+\.', r'\d+、', r'（\d+）', r'\(\d+\)']
    post_delete_patterns = [r'。\w+', r'；\w+', r'^(\w+){1,4}：', r'^\w+\[\w+\]\:', r'^\w+：']
    # split_word = ['；', '。']
    result = []

    for text in text_list:
        # print(text)
        for pattern in pre_delete_patterns:
            text = re.compile(pattern).sub('', text)
        # print(text)
        for pattern in split_patterns:
            text = re.compile(pattern).sub('$~$', text)
            
        part_result = [w for w in text.split('$~$') if len(w) > WORD_THRESHOLD]
        for part_text in part_result:
            for pattern in post_delete_patterns:
                part_text = re.compile(pattern).sub('', part_text)
            result.append(part_text)
        
    return result

def get_extra_sentence_and_vector(obj_type, obj_id):
    '''
    Args:
        - obj_type: The type of main object
        - obj_id: The id of main object
    '''
    # print(obj_id, type(obj_id), obj_id in main_job_info_bak, len(main_job_info_bak))
    if obj_type == 0:
        return (main_job_info_bak[obj_id]['require']['sentence'], 
                main_job_info_bak[obj_id]['require']['vector'])
    elif obj_type == 1:
        text = ['这属于是好福利，也就是说这属于好处。']
        return (text, None)
    
def query_top_k_index(main_vector, equal_vector, k_top=None, k_rate=None):
    '''
    Gets the first K index from the special rule

    Args:
        - main_vector: The vector of main object
        - equal_vector: The vector of qeual object
        - k_top: The first K index
        - k_rate: The first K rate index
    '''
    if k_rate != None:
        k_top = int(np.ceil(len(main_vector) * k_rate))
    k_top = min(len(main_vector), k_top)
    if not isinstance(main_vector, torch.Tensor): main_vector = torch.tensor(main_vector)
    if not isinstance(equal_vector, torch.Tensor): equal_vector = torch.tensor(equal_vector)
    
    cos_score = util.cos_sim(main_vector, equal_vector).numpy()
    scores = np.max(cos_score, axis=1, keepdims=True).reshape(1, -1)[0]
    
    return np.argsort(scores)[-k_top:]

def get_scores_by_type(type_id):
    type_name = 'jobs' if type_id == 0 else 'hunters'
    scores = both_score_info_bak[type_name]

    base_score = scores[..., 0]
    main_score = scores[..., 1]
    extra_score = scores[..., 2]

    scores = (base_score >= 0.3).astype(np.int32) * (0.7 * main_score + 0.3 * extra_score)
    # scores = (scores > 0.3).astype(np.int32) * scores
    
    return scores

_job_key_list, _job_val_list = None, None
_hunter_key_list, _hunter_val_list = None, None
def _get_obj_key_by_index(type_id, index):
    global _job_key_list, _job_val_list
    global _hunter_key_list, _hunter_val_list
    if _job_key_list == None:
        _job_key_list = list(both_info_map_bak['jobs'].keys())
        _job_val_list = list(both_info_map_bak['jobs'].values())
    if _hunter_key_list == None:
        _hunter_key_list = list(both_info_map_bak['hunters'].keys())
        _hunter_val_list = list(both_info_map_bak['hunters'].values())
    if type_id == 0:
        return _job_key_list[_job_val_list.index(index)]
    elif type_id == 1:
        return _hunter_key_list[_hunter_val_list.index(index)]

def _get_origin_item(type_id, obj_key, obj_index):
    obj_key_index = 'job_id' if type_id == 0 else 'hunter_id'
    data = job_data if type_id == 0 else hunter_data
    return data[data[obj_key_index] == int(obj_key)][obj_index].values[0]

def save_score_to_csv(type_id, scores, save_csv_file):
    assert len(scores.shape) == 2
    if type_id == 0:
        json_data = {"招聘信息ID":[], "求职者ID":[], "岗位匹配度": []}
    else:
        json_data = {"求职者ID":[], "招聘信息ID":[], "公司名称": [], "求职者满意度": []}
    main_index_len, vice_index_len = scores.shape[:2]
    sorted_index = np.argsort(-scores.reshape(1, -1)[0])
    x_indexs, y_indexs = np.unravel_index(sorted_index, scores.shape)
    total_len = main_index_len * vice_index_len
    for index in range(total_len):
        x_index, y_index = x_indexs[index], y_indexs[index]
        score = scores[x_index][y_index]
        if score <= 0.01: break
        x_key = _get_obj_key_by_index(type_id, x_index)
        y_key = _get_obj_key_by_index(type_id ^ 1, y_index)
        if type_id == 0:
            json_data['招聘信息ID'].append('\t' + str(x_key))
            json_data['求职者ID'].append('\t' + str(y_key))
            json_data['岗位匹配度'].append(score)
        elif type_id == 1:
            json_data['求职者ID'].append('\t' + str(x_key))
            json_data['招聘信息ID'].append('\t' + str(y_key))
            json_data['公司名称'].append(_get_origin_item(0, y_key, 'company_full_name'))
            json_data['求职者满意度'].append(score)

    frame_data = pd.DataFrame(json_data)
    frame_data.to_csv(save_csv_file, index=False, float_format='%.2f', encoding="GBK")