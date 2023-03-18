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

job_extra_dict = {} # id_key: {sentence: ..., vector: ..., }
hunter_extra_dict = {} # id_key: {sentence: {content: ..., vector: ...},
                       #          subject: {content: ..., vector: ...}}

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
                # print(sentence)
                obj_id = str(sentence)
                # print(obj_id)
                encode_result[obj_id] = {}
                encode_result[obj_id]['sentence'] = {}
                encode_result[obj_id]['subject'] = {} 
                continue
            
            if obj_type == 0:
                pass 
            elif obj_type == 1:
                sentence = try_to_eval(sentence)
                pass

            # print(key, type(sentence), sentence, obj_id, type(obj_id))
            encode_result[obj_id]['subject']['content'] = equal_words
            # encode_result[obj_id]['subject']['vector'] = model.encode(equal_words)
            encode_result[obj_id]['sentence']['content'] = sentence
            # encode_result[obj_id]['sentence']['vector'] = []
            # elif key == 'require':
            #     # print(ojb_id, len(sentence))
            #     sentence = multi_index_to_one(sentence)
            #     sentence = parse_long_text_list(sentence)
            #     # print(len(sentence), sentence)
            
            # if index_key != 'id':
            #     encode_result[ojb_id][key] = {}
                
                
        except Exception as e:
            print(key, e)
        
    # print(base_object_encode(ojb_id, encode_result[ojb_id]))
    # if is_modified_info_item('main', obj_type, ojb_id, encode_result[ojb_id]):
    #     for key, value in main_dict.items():
    #         if key in WITH_ENCODE_ITEMS:
    #             encode_result[ojb_id][key]['vector'] = model.encode(encode_result[ojb_id][key]['sentence'])
    # else:
    #     encode_result[ojb_id] = get_info_item('main', obj_type, ojb_id)
    # set_index_by_object_id(obj_type, ojb_id)

    dict_data.update(encode_result)
