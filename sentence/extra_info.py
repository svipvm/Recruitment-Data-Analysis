import re, time
import numpy as np
# sys.path.append('sentence')
from database_util import *
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

field_for_job = {
    'job_id': [],
    'job_welfare': ['']
}

equal_field_dcit = {} # field_key {sentence: ..., vector: ...}
job_extra_dict = {} # id_key: {sentence: ..., vector: ...}
hunter_extra_dict = {} # id_key: {sentence: ..., vector: ...}

model = get_model('extra')

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
    extra_dict = field_for_job if obj_type == 0 else field_for_hunter

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
            
            if obj_type == 0:
                pass 
            elif obj_type == 1:
                sentence = try_to_eval(sentence)
                weights = []
                if index_key == 'competition_exps':
                    for idx, text in enumerate(sentence):
                        sentence[idx] = re.sub(r'^\w+\[\w+\]:', '', text)
                        sentence[idx] = re.sub(r'(第\w+届|全国|校园|中国|国际)*', '', sentence[idx])

                        weight = re.findall(r'^\w+\[(\w+)\]:', text)
                        if len(weight) != 0: weight = weight[0]
                        grades = re.findall(r'((一|二|三|)等奖|(优秀)奖|(\w)牌)', weight)
                        grade_map = {'一': 0.4, '二': 0.3, '三': 0.2, '优秀': 0.1, 
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
                else:
                    pass

            # print(key, type(sentence), sentence, obj_id, type(obj_id))
            # encode_result[obj_id]['subject']['content'] = equal_words
            # encode_result[obj_id]['subject']['vector'] = model.encode(equal_words)
            # encode_result[obj_id]['sentence']['vector'] = []
            # elif key == 'require':
            #     # print(ojb_id, len(sentence))
            #     sentence = multi_index_to_one(sentence)
            #     sentence = parse_long_text_list(sentence)
            #     # print(len(sentence), sentence)
            
            # if index_key != ['job_id', 'hunter_id']:
            encode_result[obj_id][index_key] = {}
            encode_result[obj_id][index_key]['sentence'] = sentence
            encode_result[obj_id][index_key]['weights'] = weights
                
                
        except Exception as e:
            print(key, e)
    
    print(encode_result)
    # print(base_object_encode(ojb_id, encode_result[ojb_id]))
    if is_modified_info_item('extra', obj_type, obj_id, encode_result[obj_id]):
        for key, value in extra_dict.items():
            if key in ['job_id', 'hunter_id']: continue
            encode_result[obj_id][key]['vector'] = model.encode(encode_result[obj_id][key]['sentence'])
    else:
        encode_result[obj_id] = get_info_item('extra', obj_type, obj_id)
    # set_index_by_object_id(obj_type, ojb_id)

    dict_data.update(encode_result)
