from sentence_transformers import SentenceTransformer
import jieba, nltk, re, cpca, torch, sys, psutil, os
import pandas as pd
import numpy as np
# sys.path.append('sentence')
from database_util import *
from tqdm import tqdm

require_kind_json = { 0: '实习', 1: '不限', 2: '全职'} # self to fill
require_edu_json = { 0: '不限', 1: '技工', 2: '大专', 3: '本科', 4: '硕士', 5: '博士'}
level_json = {'COMMONLY': 1, 'GOOD': 2, 'SKILLED': 3, 'MASTER': 4}
require_edu_re_json = {'不限': 0, '技工': 1, '大专': 2, '本科': 3, '硕士': 4, '博士': 5}
with_encode_items = ['pos_name', 'pos_keys', 'skill_keys']

model = get_model()
job_data, hunter_data = get_both_data()

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
job_base_dict = {} # id_key: {sentence: ..., vector: ..., }
hunter_base_dict = {} # id_key: {sentence: ..., vector: ..., }

base_score_for_job = {} # {}
base_score_for_hunter = {}


def encode_base_data(obj, obj_type: int, dict_data: dict):
    # 0: job, 1: hunter
    assert obj_type == 0 or obj_type == 1
    encode_result = {}
    for key, value in base_dict.items():
        value = value[obj_type]
        try:
            sentence = obj[value].values.tolist()
            
            if key == 'id':
                ojb_id = str(sentence[0])
                encode_result[ojb_id] = {}
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
                encode_result[ojb_id][key] = {}
                encode_result[ojb_id][key]['sentence'] = sentence 
                    
        except Exception as e:
            print(key, e)
        
    # print(base_object_encode(ojb_id, encode_result[ojb_id]))
    if not check_base_info_item(obj_type, ojb_id, encode_result[ojb_id]):
        for key, value in base_dict.items():
            if key in with_encode_items:
                encode_result[ojb_id][key]['vector'] = model.encode(encode_result[ojb_id][key]['sentence'])
    else:
        encode_result[ojb_id] = get_base_info_item(obj_type, ojb_id)
    set_index_by_object_id(obj_type, ojb_id)

    dict_data.update(encode_result)


def calc_base_score(job_data: dict, hunter_data: dict):
    base_score = 1.0
    for key, job_item in job_data.items():
        hunter_item = hunter_data[key]
        
        sentence1, sentence2 = job_item['sentence'], hunter_item['sentence']
        if key in with_encode_items:
            vector1, vector2 = job_item['vector'], hunter_item['vector']
            score = every_multi_score(vector1, vector2)
        elif key == 'job_wage':
            sentence1 = np.mean(sentence1)
            sentence2 = np.mean(sentence2)
            sub_wage = sentence1 - sentence2
            if sub_wage > 0: score = 1
            else:
                score = max(0, 1 + sub_wage / 1000)
        elif key == 'job_kind':
            score = float(sentence1 == sentence2)
        elif key == 'exp_edu':
            score = 0.2 if len(sentence2) == 0 else float(
                        get_max_edu_level(sentence1, require_edu_re_json) <= \
                            get_max_edu_level(sentence2, require_edu_re_json))
        elif key == 'job_years':
            score = float(np.min(sentence1) <= np.max(sentence2))
        elif key == 'cor_addr':
            if re.findall(r'(.*)省', sentence1) == re.findall(r'(.*)省', sentence2):
                score = 0.5
                if re.findall(r'(.*)市', sentence1) == re.findall(r'(.*)市', sentence2):
                    score = 1
            else:
                score = 0.2
        base_score *= score
    return base_score

if __name__ == '__main__':
    # size = job_data.shape[0]
    size = 100
    for index_ in tqdm(range(size)):
        job = job_data.iloc[index_,:]
        encode_base_data(job, 0, job_base_dict)
    save_base_info_database(0, job_base_dict)

    # size = hunter_data.shape[0]
    size = 100
    for index_ in tqdm(range(size)):
        hunter = hunter_data.iloc[index_,:]
        encode_base_data(hunter, 1, hunter_base_dict)
    save_base_info_database(1, hunter_base_dict)

    save_both_info_map_database()

    expand_score_database()
    
    result = []
    for key1, job_item in job_base_dict.items():
        part_result = []
        valid_job = check_base_info_item(0, key1, job_item)
        for key2, hunter_item in hunter_base_dict.items():
            # print(job_item, hunter_item)
            valid_hunter = check_base_info_item(1, key2, hunter_item)
            if valid_job and valid_hunter:
                base_score = get_score_by_multi_id(0, key1, key2, 0)
            else:
                base_score = calc_base_score(job_item, hunter_item)
                print(key1, key2, base_score)
                set_score_by_multi_id(0, key1, key2, 0, base_score)
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

    save_both_score_info_database()
