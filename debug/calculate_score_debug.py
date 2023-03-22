import numpy as np
import pandas as pd
import json, os

os.makedirs('database', exist_ok=True)
BOTH_SCORE_INFO_BAK_FILE = 'database/both_score_info'
with open(BOTH_SCORE_INFO_BAK_FILE + '.json', 'r', encoding='GBK') as f:
    both_score_info_bak = json.loads(f.read())
print(BOTH_SCORE_INFO_BAK_FILE, 'size:', len(both_score_info_bak))

BOTH_INFO_MAP_BAK_FILE = 'database/both_info_map'
with open(BOTH_INFO_MAP_BAK_FILE + '.json', 'r', encoding='GBK') as f:
    both_info_map_bak = json.loads(f.read())
print(BOTH_INFO_MAP_BAK_FILE, 'size:', len(both_info_map_bak))

os.makedirs('datasets', exist_ok=True)
MAIN_JOB_CSV_FILE = 'datasets/result3-1.csv'
MAIN_HUNTER_CSV_FILE = 'datasets/result3-2.csv'

_job_key_list, _job_val_list = None, None
_hunter_key_list, _hunter_val_list = None, None 
def _get_obj_key_by_index(type_id, index):
    global _job_key_list, _job_val_list
    global _hunter_key_list, _hunter_val_list
    if _job_key_list == None:
        _job_key_list = list(both_info_map_bak['jobs'].keys())
        _job_val_list = list(both_info_map_bak['jobs'].values())
    if _hunter_key_list == None:
        _hunter_key_list = list(both_info_map_bak['hunters'].keys())
        _hunter_val_list = list(both_info_map_bak['hunters'].values())
    if type_id == 0:
        return _job_key_list[_job_val_list.index(index)]
    elif type_id == 1:
        return _hunter_key_list[_hunter_val_list.index(index)]


def save_score_to_csv(type_id, scores, save_csv_file):
    assert len(scores.shape) == 2
    if type_id == 0:
        json_data = {"招聘信息 ID":[], "求职者 ID":[], "岗位匹配度": []}
    else:
        json_data = {"求职者 ID":[], "招聘信息 ID":[], "公司名称": [], "求职者满意度": []}
    main_index_len, vice_index_len = scores.shape[:2]
    sorted_index = np.argsort(-scores.reshape(1, -1)[0])
    x_indexs, y_indexs = np.unravel_index(sorted_index, scores.shape)
    total_len = main_index_len * vice_index_len
    for index in range(total_len):
        x_index, y_index = x_indexs[index], y_indexs[index]
        score = scores[x_index][y_index]
        if score <= 0.01: break
        x_key = _get_obj_key_by_index(type_id, x_index)
        y_key = _get_obj_key_by_index(type_id ^ 1, y_index)
        if type_id == 0:
            json_data['招聘信息 ID'].append('\t' + str(x_key))
            json_data['求职者 ID'].append('\t' + str(y_key))
            json_data['岗位匹配度'].append(score)
        elif type_id == 1:
            json_data['求职者 ID'].append('\t' + str(x_key))
            json_data['招聘信息 ID'].append('\t' + str(y_key))
            # json_data['公司名称'].append(_get_origin_item(0, y_key, 'company_full_name'))
            json_data['公司名称'].append('none-name')
            json_data['求职者满意度'].append(score)

    frame_data = pd.DataFrame(json_data)
    frame_data.to_csv(save_csv_file, index=False, float_format='%.2f', encoding="GBK")

def get_scores_by_type(type_id):
    type_name = 'jobs' if type_id == 0 else 'hunters'
    scores = both_score_info_bak[type_name]
    if not isinstance(scores, np.ndarray): scores = np.array(scores)
    print(type_name, 'shape', scores.shape)

    base_score = scores[..., 0]
    main_score = scores[..., 1]
    extra_score = scores[..., 2]

    scores = (base_score > 0.1).astype(np.int32) * (
        0.3 * base_score + 0.5 * main_score + 0.2 * extra_score)
    
    return scores

if __name__ == '__main__':
    job_scores = get_scores_by_type(0)
    save_score_to_csv(0, job_scores, MAIN_JOB_CSV_FILE)
    hunter_scores = get_scores_by_type(1)
    save_score_to_csv(1, hunter_scores, MAIN_HUNTER_CSV_FILE)