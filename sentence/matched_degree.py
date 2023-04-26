import re, time, os
import numpy as np
from base_info import *
from main_info import *
from extra_info import *

os.makedirs('datasets', exist_ok=True)
MAIN_JOB_CSV_FILE = 'datasets/result3-1-bak.csv'
MAIN_HUNTER_CSV_FILE = 'datasets/result3-2-bak.csv'


if __name__ == '__main__':
    start_time = time.time()
    # ==================================== Begin: Base Score ====================================
    job_size = job_data.shape[0]
    # job_size = 99
    for index_ in tqdm(range(job_size), desc='Job-Base-Info'):
        job = job_data.iloc[index_,:]
        encode_base_data(job, 0, job_base_dict)
    save_info_database('base', 0, job_base_dict)
    print("Save successfully for {}/{} job base infomations.".format(
        len(job_base_dict), job_size
    ))

    hunter_size = hunter_data.shape[0]
    # hunter_size = 101
    for index_ in tqdm(range(hunter_size), desc='Hunter-Base-Info'):
        hunter = hunter_data.iloc[index_,:]
        encode_base_data(hunter, 1, hunter_base_dict)
    save_info_database('base', 1, hunter_base_dict)
    print("Save successfully for {}/{} hunter base infomations.".format(
        len(hunter_base_dict), hunter_size
    ))

    save_both_info_map_database()
    expand_score_database()
    print("Expand successfully for score matrix.")
    # print(len(main_job_info_bak))
    
    result = []
    for key1, job_item in tqdm(job_base_dict.items(), desc='Job-Base-Score'):
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
            # part_result.append(base_score)
                
        #     break
        # result.append(part_result)

    # for inx, (job_id, job_info) in enumerate(job_base_dict.items()):
    # # for _, (hunter_id, hunter_info) in enumerate(hunter_base_dict.items()):
    #     iny = np.argmax(result, axis=1)[inx]
    #     print(show_base_info(job_base_dict, inx),
    #         '\n',
    #         show_base_info(hunter_base_dict, iny),
    #         '\nscore:',
    #         result[inx][iny])

    result = []
    for key1, hunter_item in tqdm(hunter_base_dict.items(), desc='Hunter-Base-Score'):
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
            # part_result.append(base_score)
                
        #     break
        # result.append(part_result)

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
    for index_ in tqdm(range(job_size), desc='Job-Main-Info'):
        job = job_data.iloc[index_,:]
        encode_main_data(job, 0, job_main_dict)
        # break
    save_info_database('main', 0, job_main_dict)
    print("Save successfully for job main infomation.")

    for index_ in tqdm(range(hunter_size), desc='Hunter-Main-Info'):
        hunter = hunter_data.iloc[index_,:]
        encode_main_data(hunter, 1, hunter_main_dict)
        # break
    save_info_database('main', 1, hunter_main_dict)
    print("Save successfully for hunter main infomation.")
    
    result = []
    for key1, job_item in tqdm(job_main_dict.items(), desc='Job-Main-Score'):
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
            # part_result.append(main_score)
                
        #     break
        # result.append(part_result)

    # for inx, (job_id, job_info) in enumerate(job_main_dict.items()):
    #     # for _, (hunter_id, hunter_info) in enumerate(hunter_base_dict.items()):
    #     iny = np.argmax(result, axis=1)[inx]
    #     print(show_base_info(job_main_dict, inx),
    #         '\n',
    #         show_base_info(hunter_main_dict, iny),
    #         '\nscore:',
    #         result[inx][iny])
        
    result = []
    for key1, hunter_item in tqdm(hunter_main_dict.items(), desc='Hunter-Main-Score'):
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
            # part_result.append(main_score)
    #     #     break
        # result.append(part_result)
    
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
    for index_ in tqdm(range(job_size), desc='Job-Extra-Info'):
        job = job_data.iloc[index_,:]
        encode_extra_data(job, 0, job_extra_dict)
        # break
    save_info_database('extra', 0, job_extra_dict)
    print("Save successfully for job extra infomation.")

    for index_ in tqdm(range(hunter_size), desc='Hunter-Extra-Info'):
        hunter = hunter_data.iloc[index_,:]
        encode_extra_data(hunter, 1, hunter_extra_dict)
        # break
    save_info_database('extra', 1, hunter_extra_dict)
    print("Save successfully for hunter extra infomation.")
    
    encode_equal_data()
    save_info_database('equal', None, equal_field_dict)
    print("Save successfully for equal filed infomation.")

    result = []
    for key1, job_item in tqdm(job_extra_dict.items(), desc='Job-Extra-Score'):
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
            # part_result.append(extra_score)
        #     break
        # result.append(part_result)

    result = []
    for key1, hunter_item in tqdm(hunter_extra_dict.items(), desc='Hunter-Extra-Score'):
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
                extra_score = get_score_by_multi_id(1, key1, key2, 2)
            # part_result.append(extra_score)
        #     break
        # result.append(part_result)

    save_both_score_info_database()
    print("Save successfully for all score infomation.")
    # ==================================== End: Extra Score =====================================

    # ================================= Begin: Calculate Score ==================================
    print("Calculating job score.")
    job_scores = get_scores_by_type(0)
    save_score_to_csv(0, job_scores, MAIN_JOB_CSV_FILE)
    # print(job_scores)
    # print(job_scores.shape)
    print("Calculating hunter score.")
    hunter_scores = get_scores_by_type(1)
    save_score_to_csv(1, hunter_scores, MAIN_HUNTER_CSV_FILE)
    # ================================== End: Calculate Score ===================================

    print('times:', time.time() - start_time)