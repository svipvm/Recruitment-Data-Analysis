import requests, json, time
import pandas as pd

base_url = 'https://www.5iai.com/api/resume/baseInfo/public/es?pageNumber={}'
hunter_url = 'https://www.5iai.com/api/resume/baseInfo/public/{}'

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "br, gzip, deflate",
    "Accept-Language": "zh-cn",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
}

frame_json = {}

def get_one_hunter_information(data_json):
    # print(data_json)
    response = requests.get(hunter_url.format(data_json['id']), headers=headers)
    data = json.loads(response.text)

    try:
        data = data['data']
    except:
        return False
    # print(data)

    items_json = {
        'job_id': '\t' + str(data['id']),
        'hunter_name': data['username'],
        'hunter_sex': data['gender'],
        'hunter_bthday': data['birthday'],
        'hunter_addr': ''.join(eval(data['address'])),
        'hunter_addr': data['exp'],
        'hunter_sociality': data['politicalStatus'],
        'hunter_eval': data['selfEvaluation'],
        'exp_position': ','.join(eval(data['expectPosition'])),
        'exp_min_wage': data['willSalaryStart'],
        'exp_max_wage': data['willSalaryEnd'],
        # 'exp_wage_kind': data['willNature'],
        'exp_require_kind': data['willNature'],
        'exp_industry': ','.join(eval(data['expectIndustry'])),
        'exp_city': ''.join(eval(data['city'])),
        'exp_report': data['arrivalTime'],
        'resume_keys': ",".join([item['labelName'] for item in data['keywordList']]),
        # 'job_exps': [list]
        # 'work_exps': [list]
        # 'project_exps': [list]
        # 'competition_exps': [list]
        # 'education_exps': [list]
        # 'training_exps': [list]
        # 'professional_keys': [list]
        # 'skill_exps': [list]
        # 'language_exps': [list]
        # 'cert_exps': [list]
    }
    # print(items_hunter)

    if len(frame_json) == 0:
        for key, _ in items_json.items():
                frame_json[key] = []

    for key, value in items_json.items():
        frame_json[key].append(value)

    return True


def get_all_work_information():
    num_page, num_elements = 1, 1
    while True:
        response = requests.get(base_url.format(num_page))
        data = json.loads(response.text)['data']
        # print(data['content'])

        # num_elements += data['pageable']['pageSize']
        total_elements = data['totalElements']
        total_pages = data['totalPages']
        last_flag = data['last']
        print("{}/{} page running ...".format(num_page, total_pages))

        for json_item in data['content']:
            print('\t{}/{} items:'.format(num_elements, total_elements))
            try:
                if get_one_hunter_information(json_item):
                    print('\t\t[√] id ' + json_item['id'] + " finish")
                    num_elements += 1
                else:
                    print('\t\t[×] id ' + json_item['id'] + " error")
            except:
                print('\t\t[×] id ' + json_item['id'] + " exception")
            break

        break
        num_page += 1
        time.sleep(0.3)
        
        if last_flag: break


if __name__ == '__main__':
    info_csv_path = '../datasets/hunter-info.csv'

    get_all_work_information()
    frame_data = pd.DataFrame(frame_json)
    frame_data.to_csv(info_csv_path, index=False, encoding='GBK', errors='ignore')
