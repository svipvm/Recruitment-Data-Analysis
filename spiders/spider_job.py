import requests, json, time
import pandas as pd

base_url = 'https://www.5iai.com/api/enterprise/job/public/es?pageNumber={}'
work_url = 'https://www.5iai.com/api/enterprise/job/public?id={}'

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "br, gzip, deflate",
    "Accept-Language": "zh-cn",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
}

frame_json = {}

def get_one_work_information(data_json):
    # print(data_json)
    response = requests.get(work_url.format(data_json['id']), headers=headers)
    data = json.loads(response.text)

    try:
        data = data['data']
    except:
        return False
    # print(data)

    items_json = {
        'job_id': '\t' + str(data['id']),
        'company_full_name': data['enterpriseName'],
        'company_short_name': data_json['enterpriseExtInfo']['shortName'],
        'position_name': data['positionName'],
        'job_min_wage': data['minimumWage'],
        'job_max_wage': data['maximumWage'],
        'job_wage_kind': data['payMethod'],
        'require_kind': data['willNature'],
        'require_edu': data['educationalRequirements'],
        'require_exp': data['exp'],
        'num_people': data['count'],
        'deadline': data['deadline'],
        'company_ind': ','.join(eval(data_json['enterpriseExtInfo']['industry'])),
        'position_keys': ','.join([item['labelName'] for item in data['keywordList']]),
        'skill_keys': ','.join([item['labelName'] for item in data['skillsList']]),
        'job_require': ''.join(data['jobRequiredments'].split('\n')),
        'job_welfare': ','.join(eval(data['welfare'])),
        'company_addr_code': data['enterpriseAddress']['regionCode'], # 'provinceCode', 'cityCode'
        'company_addr': data['enterpriseAddress']['detailedAddress']
    }
    # print(items_json)

    if len(frame_json) == 0:
        for key, _ in items_json.items():
                frame_json[key] = []

    for key, value in items_json.items():
        frame_json[key].append(value)

    return True

def to_dataset():
    pass


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
            if get_one_work_information(json_item):
                print('\t\t[√] id ' + json_item['id'] + " finish")
                num_elements += 1
            else:
                print('\t\t[×] id ' + json_item['id'] + " error")

        num_page += 1
        time.sleep(0.3)
        
        if last_flag: break


if __name__ == '__main__':
    info_csv_path = '../datasets/recruitment-info.csv'
    # job_csv_path = '../datasets/recruitment-info.csv'

    SPIDER, DATASET = True, False
    if SPIDER:
        get_all_work_information()
        frame_data = pd.DataFrame(frame_json)
        frame_data.to_csv(info_csv_path, index=False, encoding='GBK', errors='ignore')
