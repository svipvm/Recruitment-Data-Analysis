import re, time
import numpy as np
from base_info import *
from main_info import *
from extra_info import *


if __name__ == '__main__':
    start_time = time.time()
    # size = job_data.shape[0]
    # ==================================== Begin: Base Score ====================================
    size = 5
    for index_ in tqdm(range(size), desc='Job-Base-Info'):
        job = job_data.iloc[index_,:]
        encode_base_data(job, 0, job_base_dict)
    save_info_database('base', 0, job_base_dict)

    # size = hunter_data.shape[0]
    # size = 10
    for index_ in tqdm(range(size), desc='Hunter-Base-Info'):
        hunter = hunter_data.iloc[index_,:]
        encode_base_data(hunter, 1, hunter_base_dict)
    save_info_database('base', 1, hunter_base_dict)

    save_both_info_map_database()
    expand_score_database()
    # print(len(main_job_info_bak))
    
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

    # ===================================== End: Base Score =====================================

    # ==================================== Begin: Main Score ====================================
    for index_ in tqdm(range(size), desc='Job-Main-Info'):
        job = job_data.iloc[index_,:]
        encode_main_data(job, 0, job_main_dict)
        # break
    save_info_database('main', 0, job_main_dict)

    for index_ in tqdm(range(size), desc='Hunter-Main-Info'):
        hunter = hunter_data.iloc[index_,:]
        encode_main_data(hunter, 1, hunter_main_dict)
        # break
    save_info_database('main', 1, hunter_main_dict)
    
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

    # ===================================== End: Main Score =====================================

    # =================================== Begin: Extra Score ====================================
    for index_ in tqdm(range(size), desc='Job-Extra-Info'):
        job = job_data.iloc[index_,:]
        encode_extra_data(job, 0, job_extra_dict)
        # break
    save_info_database('extra', 0, job_extra_dict)

    for index_ in tqdm(range(size), desc='Hunter-Extra-Info'):
        hunter = hunter_data.iloc[index_,:]
        encode_extra_data(hunter, 1, hunter_extra_dict)
        # break
    save_info_database('extra', 1, hunter_extra_dict)
    
    encode_equal_data()
    if DEBUG: save_info_database('equal', None, equal_field_dict)

    result = []
    for key1, job_item in job_extra_dict.items():
        part_result = []
        valid_job = info_is_modified(0, key1)
        main_sentence, main_vector = get_extra_sentence_and_vector(0, key1)
        if main_vector is None: main_vector = base_model.encode(main_sentence)
        for key2, hunter_item in hunter_extra_dict.items():
            valid_hunter = info_is_modified(1, key2)
            if valid_job or valid_hunter:
                extra_score = calc_extra_score(0, main_vector, key2, hunter_item)
                set_score_by_multi_id(0, key1, key2, 2, extra_score)
            else:
                extra_score = get_score_by_multi_id(0, key1, key2, 2)
            part_result.append(extra_score)
        #     break
        result.append(part_result)

    result = []
    for key1, hunter_item in hunter_extra_dict.items():
        part_result = []
        valid_hunter = info_is_modified(1, key1)
        main_sentence, main_vector = get_extra_sentence_and_vector(1, key1)
        if main_vector is None: main_vector = base_model.encode(main_sentence)
        for key2, job_item in job_extra_dict.items():
            valid_job = info_is_modified(0, key2)
            if valid_job or valid_hunter:
                extra_score = calc_extra_score(1, main_vector, key2, job_item)
                set_score_by_multi_id(1, key1, key2, 2, extra_score)
            else:
                extra_score = get_score_by_multi_id(0, key1, key2, 2)
            part_result.append(extra_score)
        #     break
        result.append(part_result)

    # ==================================== End: Extra Score =====================================

    save_both_score_info_database()


    print('times:', time.time() - start_time)