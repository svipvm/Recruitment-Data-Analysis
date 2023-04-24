import re, time
import numpy as np
# sys.path.append('sentence')
from database_util import *
import traceback
from tqdm import tqdm

field_for_hunter = {
    'hunter_id': [],
    'competition_exps': ['竞赛经历'],
    'education_exps': ['教育经历', '学历要求'],
    'training_exps': ['培训经历', '实习经历'],
    'skill_exps': ['掌握技能', '掌握工具'],
    'language_exps': ['掌握交流语言', '外语能力'],
    'cert_exps': ['各方面能力'],
}
extra_hunter_score_weights = {
    'competition_exps': 6,
    'education_exps': 3,
    'training_exps': 6,
    'skill_exps': 5,
    'language_exps': 5,
    'cert_exps': 2,
}
extra_hunter_score_sum = np.sum([weight for _, weight in extra_hunter_score_weights.items()])
for key, weight in extra_hunter_score_weights.items():
    extra_hunter_score_weights[key] = weight / extra_hunter_score_sum

field_for_job = {
    'job_id': [],
    'job_welfare': ['额外福利', '工作福利']
}
extra_job_score_weights = {
    'job_welfare': 1
}
extra_job_score_sum = np.sum([weight for _, weight in extra_job_score_weights.items()])
for key, weight in extra_job_score_weights.items():
    extra_job_score_weights[key] = weight / extra_job_score_sum
if DEBUG: print('extra score weights:\n', '\t', extra_hunter_score_weights, 
                '\n\t', extra_job_score_weights)

job_extra_dict = {} # id_key: {sentence: ..., vector: ...}
hunter_extra_dict = {} # id_key: {sentence: ..., vector: ...}

extra_model = get_model('extra')

def encode_extra_data(obj, obj_type: int, dict_data: dict):
    '''
    Read information from the backup database into the dictionary

    Args:
        - obj: The framedata object to be extracted
        - obj_type: The type of the object
        - dict_data: Dictionary to store
    Returns: None
    '''
    assert obj_type == 0 or obj_type == 1
    obj_name = 'job' if obj_type == 0 else 'hunter'
    extra_dict = field_for_job if obj_type == 0 else field_for_hunter

    if obj_name not in equal_field_dict: 
        equal_field_dict[obj_name] = {}
        for key, value in extra_dict.items():
            if key == 'job_id' or key == 'hunter_id': continue
            equal_field_dict[obj_name][key] = {}
            equal_field_dict[obj_name][key]['sentence'] = value
            equal_field_dict[obj_name][key]['vector'] = extra_model.encode(value)

    # {id: {sentence: ...}, pos_name: {sentence: ..., vector: ...}, ...}
    encode_result = {} 
    for key, value in extra_dict.items():
        # value = value[obj_type]
        index_key, equal_words = key, value
        try:
            # print(index_key, obj)
            sentence = obj[index_key]
            # print(index_key == 'hunter_id', key, type(sentence), sentence)
            # print(key, sentence)
            
            if index_key == 'job_id' or index_key == 'hunter_id':
                obj_id = str(sentence)
                encode_result[obj_id] = {}
                continue
            
            sentence = try_to_eval(sentence)
            if obj_type == 0:
                weights = []
                if index_key == 'job_welfare':
                    weights = [0.3] * len(sentence)
            elif obj_type == 1:
                # sentence = try_to_eval(sentence)
                weights = []
                for idx, text in enumerate(sentence):
                    if index_key == 'competition_exps':
                        sentence[idx] = re.sub(r'^\w+\[\w+\]:', '', text)
                        sentence[idx] = re.sub(r'(第\w+届|全国|校园|中国|国际)*', '', sentence[idx])

                        # weight = re.findall(r'^\w+\[(\w+)\]:', text)
                        weight = re.findall(r'^\w+\[(.*?)(、|\])', text)
                        if len(weight) != 0: weight = weight[0][0]
                        grades = re.findall(r'((一|二|三|)等奖|优(秀|胜)奖|(\w)牌)', weight)
                        grade_map = {'一': 0.4, '二': 0.3, '三': 0.2, '秀': 0.1, '胜': 0.1, 
                                     '金': 0.4, '银': 0.3, '铜': 0.2}
                        # print(grades)
                        if len(grades) > 0:
                            # print(grades[0])
                            grades = [grade for grade in grades[0] if len(grade) > 0]
                            # print(grades)
                            try:
                                grade = grade_map[grades[1]]
                            except:
                                grade = 0.1
                        else:
                            grade = 0
                        if '全国' in text: grade += 0.5
                        weights.append(grade)
                    # print(weights)
                    elif index_key == 'education_exps':
                    # for idx, text in enumerate(sentence):
                        sentence[idx] = re.sub(r'^\w+\[\w+\]:', '', text)

                        weight = re.findall(r'^\w+\[(\w+)\]:', text)
                        if len(weight) != 0: weight = weight[0]
                        try:
                            grade = require_edu_re_json[weight]
                        except:
                            grade = 0
                        # print(weight)
                        weights.append(grade)
                    elif index_key == 'training_exps':
                    # for idx, text in enumerate(sentence): 
                        sentence[idx] = re.findall(r'\[(\w+)\]', text)[0]
                        weights.append(0.8)
                    elif index_key == 'skill_exps' or index_key == 'language_exps':
                    # for idx, text in enumerate(sentence): 
                        sentence[idx] = re.sub(r'\[(\w+)\]', '', text)
                        weight = re.findall(r'\[(\w+)\]', text)
                        if len(weight) != 0: weight = weight[0]
                        try:
                            grade = 0.2 * level_json[weight]
                        except:
                            grade = 0
                        weights.append(grade)
                    elif index_key == 'cert_exps':
                    # for idx, text in enumerate(sentence):
                        sentence[idx] = re.sub(r'\[(\w+)\]', '', text)
                        weights.append(0.6)
                # else:
                #     pass
            
            # if index_key != ['job_id', 'hunter_id']:
            encode_result[obj_id][index_key] = {}
            encode_result[obj_id][index_key]['sentence'] = sentence
            encode_result[obj_id][index_key]['weights'] = weights
                
        except Exception as e:
            print(obj_id, key, weight, e)
            traceback.print_exc()
    
    # print(encode_result)
    # print(base_object_encode(ojb_id, encode_result[ojb_id]))
    if is_modified_info_item('extra', obj_type, obj_id, encode_result[obj_id]):
        for key, value in extra_dict.items():
            if key in ['job_id', 'hunter_id']: continue
            encode_result[obj_id][key]['vector'] = extra_model.encode(encode_result[obj_id][key]['sentence'])
        set_info_item('extra', obj_type, obj_id, encode_result[obj_id])
    else:
        encode_result[obj_id] = get_info_item('extra', obj_type, obj_id)
    # set_index_by_object_id(obj_type, ojb_id)

    dict_data.update(encode_result)

def encode_equal_data():
    for obj_type in [0, 1]:
        obj_name = 'job' if obj_type == 0 else 'hunter'
        extra_dict = field_for_job if obj_type == 0 else field_for_hunter
        if obj_name not in equal_field_dict: 
            equal_field_dict[obj_name] = {}
            for key, value in extra_dict.items():
                if key == 'job_id' or key == 'hunter_id': continue
                equal_field_dict[obj_name][key] = {}
                equal_field_dict[obj_name][key]['sentence'] = value
                equal_field_dict[obj_name][key]['vector'] = extra_model.encode(value)

def calc_extra_score(obj_type: int, main_vector, vice_id, vice_obj: dict):
    '''
    From the point of view of the main object, calculate the extra score of the vice object

    Args:
        - obj_type: The type of the main object
        - vice_obj: vice object
    Returns: The extra score
    '''
    vice_obj_name = 'job' if obj_type == 1 else 'hunter'
    score_weights = extra_job_score_weights if obj_type == 1 else extra_hunter_score_weights
    # if obj_type == 0:
    #     item_base_score = 1 / (len(field_for_hunter) - 1)
    # else:
    #     item_base_score = 1 / (len(field_for_job) - 1)
    extra_score = 0.0
    # main_sentence, main_vector = get_extra_sentence_and_vector(obj_type, main_id)
    # if main_vector is None: main_vector = model.encode(main_sentence)
    # print(main_sentence, len(main_vector))
    # vice_dict = job_extra_dict if obj_type == 1 else hunter_extra_dict

    for key, vice_item in vice_obj.items():
        # print(key, len(vice_item))
        sentence = vice_item['sentence']
        weights = vice_item['weights']
        vice_vector = vice_item['vector']
        equal_vector = equal_field_dict[vice_obj_name][key]['vector']

        # print(len(main_vector))
        try:
            if len(vice_vector) == 0: continue
            main_vector_index = query_top_k_index(main_vector, equal_vector, k_rate=0.7)
            # print(main_vector_index)
            if len(main_vector_index) == 0: continue
            score = every_multi_score(main_vector[main_vector_index], vice_vector, 'weights', weights)
        except Exception as e:
            print(e, len(main_vector))
        # score = 0.5
    #     vice_item = vice_obj[key]
    #     sentence1, sentence2 = main_item['sentence'], vice_item['sentence']

    #     # if key ontin WITH_ENCODE_ITEMS:
    #     vector1, vector2 = main_item['vector'], vice_item['vector']
    #     if obj_type == 0: 
    #         if len(vector1) == 0 or len(vector2) == 0: score = 0.1
    #         else: score = every_multi_score(vector1, vector2, 'mean')
    #     else:
    #         if len(vector1) == 0 or len(vector2) == 0: score = 0.1
    #         else: score = every_multi_score(vector1, vector2, 'k-mean')
        
        # extra_score += item_base_score * score
        if score < 1e-8: score = 0
        extra_score += score * score_weights[key]

    return extra_score

