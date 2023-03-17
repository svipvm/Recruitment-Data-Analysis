from sentence_transformers import SentenceTransformer, util
import cpca, re, json, torch
import numpy as np
import pandas as pd

job_csv_file = 'datasets/recruitment-info.csv'
hunter_csv_file = 'datasets/hunter-info.csv'
job_data = pd.read_csv(job_csv_file, encoding='GBK')
hunter_data = pd.read_csv(hunter_csv_file, encoding='GBK')

base_job_info_bak_file = 'database/base_job_info.json'
try:
    with open(base_job_info_bak_file, 'r') as f:
        base_job_info_bak = f.read()
        base_job_info_bak = json.loads(base_job_info_bak)
except:
    base_job_info_bak = {}

base_hunter_info_bak_file = 'database/base_hunter_info.json'
try:
    with open(base_hunter_info_bak_file, 'r') as f:
        base_hunter_info_bak = f.read()
        base_hunter_info_bak = json.loads(base_hunter_info_bak)
except:
    base_hunter_info_bak = {}

both_info_map_bak_file = 'database/both_info_map.json'
try:
    with open(both_info_map_bak_file, 'r') as f:
        both_info_map_bak = f.read()
        both_info_map_bak = json.loads(both_info_map_bak)
except:
    both_info_map_bak = {}

model_path = '/home/vmice/projects/sbert-base-chinese-nli'
model = SentenceTransformer(model_path)

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def get_model():
    return model

def get_both_data():
    return job_data, hunter_data

def multi_index_to_one(item_list):
    if isinstance(item_list, str):
        return [item_list]
    result = None
    for item in item_list:
        if not result:
            result = eval(item) 
            result += eval(item)
    return result

def try_to_eval(item):
    try:
        return eval(item)
    except:
        return [item]
    
def change_wage(min_wage, max_wage, wage_kind=1):
    return [min_wage // 12, max_wage // 12] if wage_kind == 0 \
        else ([min_wage * 30, max_wage * 30] if wage_kind == 2 else [min_wage, max_wage])

def change_addrs(addrs):
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
    return [re.findall(r'\[(.*)\]', edu)[0] for edu in edus]

def delete_same_elem(list_like):
    return np.unique(np.array(list_like)).tolist()

def change_years(years):
    years = re.findall(r'(\d+)', years)
    years = [int(year) for year in years]
    if len(years) == 0: years = [0]
    return years

def every_multi_score(vector1, vector2, method='mean'):
    if not isinstance(vector1, torch.Tensor): vector1 = torch.tensor(vector1)
    if not isinstance(vector2, torch.Tensor): vector2 = torch.tensor(vector2)
    if vector1.shape[0] == 0: return 1
    if vector2.shape[0] == 0: return 0.6
    # print(vector1.shape, vector2.shape)
    cos_score = util.cos_sim(vector1, vector2).numpy()
    scores = [np.max(cos_score[i, :], keepdims=False) for i in range(cos_score.shape[0])]
    if method == 'mean':
        multi_score = np.mean(scores)
    else:
        multi_score = np.dot(scores, [1] * len(scores))
    return multi_score

def get_max_edu_level(sentence, level_json):
    level = [level_json[edu] for edu in sentence]
    return np.max(level, keepdims=False)

def show_base_info(base_dict, index):
    return '。'.join([str(value['sentence']) for _, value in base_dict[list(base_dict.keys())[index]].items()])

def base_object_encode(info_id, info_dict: dict):
    return '。'.join([info_id] + [str(value['sentence']) for _, value in info_dict.items()])

def check_base_info_item(obj_type, info_id, info_dict):
    item_value = base_object_encode(info_id, info_dict)
    base_info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    if info_id not in base_info_bak:
        return False
    else:
        item_back_value = base_object_encode(info_id, base_info_bak[info_id])
        return item_back_value == item_value

def get_base_info_item(obj_type, info_id):
    base_info_bak = base_job_info_bak if obj_type == 0 else base_hunter_info_bak
    assert info_id in base_info_bak
    return base_info_bak[info_id]

def save_base_info_database(obj_type, data_dict):
    base_info_bak_file = base_job_info_bak_file if obj_type == 0 else base_hunter_info_bak_file
    # print(type(data_dict))
    with open(base_info_bak_file, 'w') as f:
        f.write(json.dumps(data_dict, cls=NpEncoder))

def get_index_by_object_id(obj_type, obj_id):
    obj_name = 'job' if obj_type == 0 else 'hunters'
    if obj_id in both_info_map_bak[obj_name]:
        return both_info_map_bak[obj_name][obj_id]
    else:
        return -1
    
def set_index_by_object_id(obj_type, obj_id):
    obj_name = 'job' if obj_type == 0 else 'hunters'
    if obj_name not in both_info_map_bak:
        both_info_map_bak[obj_name] = {}
    if obj_id not in both_info_map_bak[obj_name]:
        both_info_map_bak[obj_name][obj_id] = len(both_info_map_bak[obj_name])

def save_both_info_map_database():
    with open(both_info_map_bak_file, 'w') as f:
        f.write(json.dumps(both_info_map_bak, cls=NpEncoder))
