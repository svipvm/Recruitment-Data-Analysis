import re, time
import numpy as np
# sys.path.append('sentence')
from database_util import *
from tqdm import tqdm

require_kind_json = { 0: '实习', 1: '不限', 2: '全职'} # self to fill
require_edu_json = { 0: '不限', 1: '技工', 2: '大专', 3: '本科', 4: '硕士', 5: '博士'}
WITH_ENCODE_ITEMS = ['pos_name', 'pos_keys', 'skill_keys']

base_dict = {
    'id': (['job_id'], ['hunter_id']),
    'pos_name': (['position_name'], ['exp_position']),
    'job_wage': (['job_min_wage', 'job_max_wage', 'job_wage_kind'], ['exp_min_wage', 'exp_max_wage']),
    'job_kind': (['require_kind'], ['exp_require_kind']),
    'exp_edu': (['require_edu'], ['education_exps']),
    'job_years': (['require_exp'], ['hunter_exp']),
    'pos_keys': (['position_keys', 'company_ind'], ['exp_industry']),
    'cor_addr': (['company_addr', 'company_full_name'], ['exp_city']),
    'skill_keys': (['skill_keys'], ['skill_exps'])
}
base_score_weights = {
    'pos_name': 3,
    'job_wage': 2,
    'job_kind': 3,
    'exp_edu': 2,
    'job_years': 2,
    'pos_keys': 3,
    'cor_addr': 2,
    'skill_keys': 3,
}
base_score_sum = np.sum([weight for _, weight in base_score_weights.items()])
for key, weight in base_score_weights.items():
    base_score_weights[key] = weight / base_score_sum
if DEBUG: print('base score weights:\n', '\t', base_score_weights)

job_base_dict = {} # id_key: {sentence: ..., vector: ..., }
hunter_base_dict = {} # id_key: {sentence: ..., vector: ..., }

# base_score_for_job = {} # {}
# base_score_for_hunter = {}
base_model = get_model('base')


def encode_base_data(obj, obj_type: int, dict_data: dict):
    '''
    Read information from the backup database into the dictionary

    Args:
        - obj: The framedata object to be extracted
        - obj_type: The type of the object
        - dict_data: Dictionary to store
    Returns: None
    '''
    assert obj_type == 0 or obj_type == 1

    # {id: {sentence: ...}, pos_name: {sentence: ..., vector: ...}, ...}
    encode_result = {} 
    for key, value in base_dict.items():
        value = value[obj_type]
        try:
            sentence = obj[value].values.tolist()
            
            if key == 'id':
                obj_id = str(sentence[0])
                encode_result[obj_id] = {}
            elif key == 'pos_name':
                sentence = try_to_eval(sentence[0])
                sentence = [word.replace('实习生', '') for word in sentence]
            elif key == 'job_wage':
                sentence = change_wage(*sentence)
            elif key == 'job_kind':
                try:
                    sentence = require_kind_json[int(sentence[0])]
                except:
                    sentence = require_kind_json[1]
            elif key == 'exp_edu':
                try:
                    sentence = [require_edu_json[sentence[0]]]
                except:
                    sentence = change_edus(try_to_eval(sentence[0]))
            elif key == 'job_years':
                try:
                    sentence = change_years(sentence[0])
                except:
                    sentence = [0]
            elif key == 'pos_keys':
                sentence = delete_same_elem(multi_index_to_one(sentence))
            elif key == 'cor_addr':
                sentence = change_addrs(sentence)
            elif key == 'skill_keys':
                sentence = multi_index_to_one(sentence)
            
            if key != 'id':
                encode_result[obj_id][key] = {}
                encode_result[obj_id][key]['sentence'] = sentence 
                    
        except Exception as e:
            print(key, e)
        
    # print(base_object_encode(ojb_id, encode_result[ojb_id]))
    if is_modified_info_item('base', obj_type, obj_id, encode_result[obj_id]):
        for key, value in base_dict.items():
            if key in WITH_ENCODE_ITEMS:
                encode_result[obj_id][key]['vector'] = base_model.encode(encode_result[obj_id][key]['sentence'])
        set_info_item('base', obj_type, obj_id, encode_result[obj_id])
    else:
        encode_result[obj_id] = get_info_item('base', obj_type, obj_id)
    set_index_by_object_id(obj_type, obj_id)

    dict_data.update(encode_result)


def calc_base_score(obj_type: int, main_obj: dict, vice_obj: dict):
    '''
    From the point of view of the main object, calculate the basic score of the vice object

    Args:
        - obj_type: The type of the main object
        - main_obj: main object
        - vice_obj: vice object
    Returns: The basic score
    '''
    pos_name_threshold = 0.2
    base_score = 0.0
    for key, main_item in main_obj.items():
        vice_item = vice_obj[key]
        sentence1, sentence2 = main_item['sentence'], vice_item['sentence']

        if key in WITH_ENCODE_ITEMS:
            vector1, vector2 = main_item['vector'], vice_item['vector']
            if obj_type == 0:
                if len(vector1) == 0: score = 1
                elif len(vector2) == 0: score = 0.3
                else: score = every_multi_score(vector1, vector2, 'mean')
            else:
                if len(vector1) == 0 or len(vector2) == 0: score = 1
                else: score = every_multi_score(vector1, vector2, 'max')
        elif key == 'job_wage':
            sentence1 = np.mean(sentence1)
            sentence2 = np.mean(sentence2)
            sub_wage = sentence1 - sentence2
            dc = 1 if obj_type == 0 else -1
            score = 1 if dc * sub_wage > 0 else max(0, 1 + dc * sub_wage / 1000)
        elif key == 'job_kind':
            score = float(sentence1 == sentence2)
        elif key == 'exp_edu':
            if obj_type == 0:
                score = 0.2 if len(sentence2) == 0 else float(
                            get_max_edu_level(sentence1, require_edu_re_json) <= \
                                get_max_edu_level(sentence2, require_edu_re_json))
            else:
                score = 1 if len(sentence2) == 0 else float(
                            get_max_edu_level(sentence1, require_edu_re_json) >= \
                                get_max_edu_level(sentence2, require_edu_re_json))
        elif key == 'job_years':
            if obj_type == 0:
                score = float(np.min(sentence1) <= np.max(sentence2))
            else:
                score = float(np.min(sentence1) >= np.max(sentence2))
        elif key == 'cor_addr':
            if re.findall(r'(.*)省', sentence1) == re.findall(r'(.*)省', sentence2):
                score = 0.5
                if re.findall(r'(.*)市', sentence1) == re.findall(r'(.*)市', sentence2):
                    score = 1
            else:
                score = 0.2

        if score <= 1e-6 or (key == 'pos_name' and score < pos_name_threshold): return 0
        base_score += score * base_score_weights[key]
    return base_score

if __name__ == '__main__':
    start_time = time.time()
    # size = job_data.shape[0]
    size = 100
    for index_ in tqdm(range(size)):
        job = job_data.iloc[index_,:]
        encode_base_data(job, 0, job_base_dict)
    save_info_database('base', 0, job_base_dict)

    # size = hunter_data.shape[0]
    size = 100
    for index_ in tqdm(range(size)):
        hunter = hunter_data.iloc[index_,:]
        encode_base_data(hunter, 1, hunter_base_dict)
    save_info_database('base', 1, hunter_base_dict)

    save_both_info_map_database()

    expand_score_database()
    
    result = []
    for key1, job_item in job_base_dict.items():
        part_result = []
        valid_job = info_is_modified(0, key1)
        for key2, hunter_item in hunter_base_dict.items():
            # print(job_item, hunter_item)
            valid_hunter = info_is_modified(1, key2)
            if valid_job or valid_hunter:
                base_score = calc_base_score(0, job_item, hunter_item)
                # print(key1, key2, base_score)
                set_score_by_multi_id(0, key1, key2, 0, base_score)
            else:
                base_score = get_score_by_multi_id(0, key1, key2, 0)
            part_result.append(base_score)
                
        #     break
        result.append(part_result)

    # for inx, (job_id, job_info) in enumerate(job_base_dict.items()):
    # # for _, (hunter_id, hunter_info) in enumerate(hunter_base_dict.items()):
    #     iny = np.argmax(result, axis=1)[inx]
    #     print(show_base_info(job_base_dict, inx),
    #         '\n',
    #         show_base_info(hunter_base_dict, iny),
    #         '\nscore:',
    #         result[inx][iny])

    result = []
    for key1, hunter_item in hunter_base_dict.items():
        part_result = []
        valid_hunter = info_is_modified(1, key1)
        for key2, job_item in job_base_dict.items():
            # print(job_item, hunter_item)
            valid_job = info_is_modified(0, key2)
            if valid_job or valid_hunter:
                base_score = calc_base_score(1, hunter_item, job_item)
                # print(key1, key2, base_score)
                set_score_by_multi_id(1, key1, key2, 0, base_score)
            else:
                base_score = get_score_by_multi_id(1, key1, key2, 0)
            part_result.append(base_score)
                
        #     break
        result.append(part_result)

    # for inx, (hunter_id, hunter_info) in enumerate(hunter_base_dict.items()):
    # # for _, (hunter_id, hunter_info) in enumerate(hunter_base_dict.items()):
    #     iny = np.argmax(result, axis=1)[inx]
    #     print(show_base_info(job_base_dict, iny),
    #         '\n',
    #         show_base_info(hunter_base_dict, inx),
    #         '\nscore:',
    #         result[inx][iny])

    save_both_score_info_database()

    print('times:', time.time() - start_time)