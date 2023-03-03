import requests, json
import pandas as pd
from bs4 import BeautifulSoup

base_url = 'https://www.5iai.com/api/enterprise/job/public/es?pageNumber={}'
# work_home_url = 'https://www.5iai.com/#/jobDetails/{}'
work_url = 'https://www.5iai.com/api/enterprise/job/public?id={}'

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "br, gzip, deflate",
    "Accept-Language": "zh-cn",
    # "Host": "httpbin.org",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
}

# response = requests.get(work_home_url.format(1613439889204969472), headers=headers)
# soup = BeautifulSoup(response.text, features='lxml')
# print(soup)
# print(soup.find(attrs={'class': 'txtCutter'}))

response = requests.get(work_url.format(1613439889204969472))
data = json.loads(response.text)
if data['status'] != 200:
    print("Error")
    # error operation
data = data['data']


# 工作地点其一: workplace
# 地点代码： enterpriseAddress

items_json = {
    'enterprise_name': data['enterpriseName'],
    'position_name': data['positionName'],
    'min_wage': data['minimumWage'],
    'max_wage': data['maximumWage'],
    'wage_kind': data['payMethod'],
    'work_kind': data['willNature'],
    'education': data['educationalRequirements'],
    'exp_reange': data['exp'],
    'enrollment': data['count'],
    'deadline': data['deadline'],
    'position_keys': ','.join([item['labelName'] for item in data['keywordList']]),
    'skill_keys': ','.join([item['labelName'] for item in data['skillsList']]),
    'job_require': data['jobRequiredments'],
    'welfare': data['welfare'],
}
print(items_json)

frame_json = {
    'enterprise_name': [],
    'position_name': [],
    'min_wage': [],
    'max_wage': [],
    'wage_kind': [],
    'work_kind': [],
    'education': [],
    'exp_reange': [],
    'enrollment': [],
    'deadline': [],
    'position_keys': [],
    'skill_keys': [],
    'job_require': [],
    'welfare': [],
}

for key, value in items_json.items():
    frame_json[key].append(value)

frame_data = pd.DataFrame(frame_json)
frame_data.to_csv('./result1-1-expand.csv', index_label="序号", index=1, encoding='GB2312')
# frame_data = {"招聘信息ID": [],
#               "企业名称": [],
#               "招聘岗位": []}
# response = requests.get(base_url.format(158))
# data = json.loads(response.text)['data']
# num_item = data['pageable']['pageSize']
# total_elements = data['totalElements']
# page_number = data['pageable']['pageNumber']
# total_pages = data['totalPages']
# last_flag = data['last']

# print("{}/{} page: {}/{} items".format(page_number, total_pages, num_item, total_elements))
# print(last_flag)
# # print(data['content'])

# for work_item in data['content']:
#     work_id = work_item['id']
#     work_response = requests.get('https://www.5iai.com/#/jobDetails/{}'.format(work_id))
#     print(work_id)
#     # print(work_item)
#     break