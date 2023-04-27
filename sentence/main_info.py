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
main_score_weights = {
    'require': 1,
}
main_score_sum = np.sum([weight for _, weight in main_score_weights.items()])
for key, weight in main_score_weights.items():
    main_score_weights[key] = weight / main_score_sum
if DEBUG: print('main score weights:\n', '\t', main_score_weights)

job_main_dict = {} # id_key: {sentence: ..., vector: ..., }
hunter_main_dict = {} # id_key: {sentence: ..., vector: ..., }

main_model = get_model('main')

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
                obj_id = str(sentence[0])
                encode_result[obj_id] = {}
            elif key == 'require':
                # print(ojb_id, len(sentence))
                sentence = multi_index_to_one(sentence)
                sentence = parse_long_text_list(sentence)
                # print(len(sentence), sentence)
            
            if key != 'id':
                encode_result[obj_id][key] = {}
                encode_result[obj_id][key]['sentence'] = sentence 
                
        except Exception as e:
            print(key, e)
        
    # print(base_object_encode(ojb_id, encode_result[ojb_id]))
    if is_modified_info_item('main', obj_type, obj_id, encode_result[obj_id]):
        for key, value in main_dict.items():
            if key in WITH_ENCODE_ITEMS:
                encode_result[obj_id][key]['vector'] = main_model.encode(encode_result[obj_id][key]['sentence'])
        set_info_item('main', obj_type, obj_id, encode_result[obj_id])
    else:
        encode_result[obj_id] = get_info_item('main', obj_type, obj_id)
    set_index_by_object_id(obj_type, obj_id)

    dict_data.update(encode_result)


def calc_main_score(obj_type: int, main_obj: dict, vice_obj: dict):
    '''
    From the point of view of the main object, calculate the main score of the vice object

    Args:
        - obj_type: The type of the main object
        - main_obj: main object
        - vice_obj: vice object
    Returns: The main score
    '''
    main_score = 0.0
    for key, main_item in main_obj.items():
        vice_item = vice_obj[key]
        sentence1, sentence2 = main_item['sentence'], vice_item['sentence']

        if key in WITH_ENCODE_ITEMS:
            vector1, vector2 = main_item['vector'], vice_item['vector']
            if obj_type == 0: 
                if len(vector1) == 0 or len(vector2) == 0: score = 0.5
                else: score = every_multi_score(vector1, vector2, 'mean')
            else:
                if len(vector1) == 0 or len(vector2) == 0: score = 0.5
                else: score = every_multi_score(vector1, vector2, 'k-mean')
        if score < 1e-8: score = 0
        main_score += score * main_score_weights[key]

    return main_score

if __name__ == '__main__':
    start_time = time.time()
    # size = job_data.shape[0]
    size = 15
    for index_ in tqdm(range(size)):
        job = job_data.iloc[index_,:]
        encode_main_data(job, 0, job_main_dict)
        # break
    save_info_database('main', 0, job_main_dict)

    # size = job_data.shape[1]
    size = 15
    for index_ in tqdm(range(size)):
        hunter = hunter_data.iloc[index_,:]
        encode_main_data(hunter, 1, hunter_main_dict)
        # break
    save_info_database('main', 1, hunter_main_dict)

    save_both_info_map_database() # only one
    expand_score_database() # only one

    result = []
    for key1, job_item in job_main_dict.items():
        part_result = []
        valid_job = info_is_modified(0, key1)
        for key2, hunter_item in hunter_main_dict.items():
            # print(job_item, hunter_item)
            valid_hunter = info_is_modified(1, key2)
            if valid_job or valid_hunter:
                main_score = calc_main_score(0, job_item, hunter_item)
                # print(key1, key2, base_score)
                set_score_by_multi_id(0, key1, key2, 1, main_score)
            else:
                main_score = get_score_by_multi_id(0, key1, key2, 1)
            part_result.append(main_score)
                
        #     break
        result.append(part_result)

    # for inx, (job_id, job_info) in enumerate(job_main_dict.items()):
    #     # for _, (hunter_id, hunter_info) in enumerate(hunter_base_dict.items()):
    #     iny = np.argmax(result, axis=1)[inx]
    #     print(show_base_info(job_main_dict, inx),
    #         '\n',
    #         show_base_info(hunter_main_dict, iny),
    #         '\nscore:',
    #         result[inx][iny])
        
    result = []
    for key1, hunter_item in hunter_main_dict.items():
        part_result = []
        valid_hunter = info_is_modified(1, key1)
        for key2, job_item in job_main_dict.items():
            # print(job_item, hunter_item)
            valid_job = info_is_modified(0, key2)
            if valid_job or valid_hunter:
                main_score = calc_main_score(1, hunter_item, job_item)
                # print(key1, key2, base_score)
                set_score_by_multi_id(1, key1, key2, 1, main_score)
            else:
                main_score = get_score_by_multi_id(1, key1, key2, 1)
            part_result.append(main_score)
    #     #     break
        result.append(part_result)
    
    # for inx, (hutner_id, hunter_info) in enumerate(hunter_main_dict.items()):
    #     # for _, (hunter_id, hunter_info) in enumerate(hunter_base_dict.items()):
    #     iny = np.argmax(result, axis=1)[inx]
    #     print(show_base_info(job_main_dict, iny),
    #         '\n',
    #         show_base_info(hunter_main_dict, inx),
    #         '\nscore:',
    #         result[inx][iny])

    save_both_score_info_database() # only one

    print('times:', time.time() - start_time)