import re, time
import numpy as np
# sys.path.append('sentence')
from database_util import *
from tqdm import tqdm

WITH_ENCODE_ITEMS = ['require']

main_dict = {
    'id': (['job_id'], ['hunter_id']),
    'require': (['job_require'], ['hunter_eval', 'job_exps', 'project_exps'])
    # 'require': (['job_require'], ['hunter_eval', 'job_exps', 'project_exps', 'competition_exps', 
    #             'education_exps', 'training_exps', 'skill_exps', 'language_exps', 'cert_exps'])
}
job_main_dict = {} # id_key: {sentence: ..., vector: ..., }
hunter_main_dict = {} # id_key: {sentence: ..., vector: ..., }

model = get_model('main')

def encode_main_data(obj, obj_type: int, dict_data: dict):
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
    for key, value in main_dict.items():
        value = value[obj_type]
        try:
            sentence = obj[value].values.tolist()
            # print(key, type(sentence), sentence)
            # print(key)
            
            if key == 'id':
                ojb_id = str(sentence[0])
                encode_result[ojb_id] = {}
            elif key == 'require':
                # print(ojb_id, len(sentence))
                sentence = multi_index_to_one(sentence)
                sentence = parse_long_text_list(sentence)
                # print(len(sentence), sentence)
            
            if key != 'id':
                encode_result[ojb_id][key] = {}
                encode_result[ojb_id][key]['sentence'] = sentence 
                
        except Exception as e:
            print(key, e)
        
    # print(base_object_encode(ojb_id, encode_result[ojb_id]))
    if is_modified_info_item('main', obj_type, ojb_id, encode_result[ojb_id]):
        for key, value in main_dict.items():
            if key in WITH_ENCODE_ITEMS:
                encode_result[ojb_id][key]['vector'] = model.encode(encode_result[ojb_id][key]['sentence'])
    else:
        encode_result[ojb_id] = get_info_item('main', obj_type, ojb_id)
    set_index_by_object_id(obj_type, ojb_id)

    dict_data.update(encode_result)

if __name__ == '__main__':
    start_time = time.time()
    # size = job_data.shape[0]
    size = 100
    for index_ in tqdm(range(size)):
        job = job_data.iloc[index_,:]
        encode_main_data(job, 0, job_main_dict)
        # break
    save_info_database('main', 0, job_main_dict)

    # size = job_data.shape[1]
    size = 100
    for index_ in tqdm(range(size)):
        hunter = hunter_data.iloc[index_,:]
        encode_main_data(hunter, 1, hunter_main_dict)
        # break
    save_info_database('main', 1, hunter_main_dict)