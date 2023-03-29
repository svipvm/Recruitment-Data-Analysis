import re, json

POSITION_TYPE_FILE = './position_type.json'

with_position_suffixs = ['产品经理', '分析师', '工程师', '开发', '测试', '岗', '支持', '运维', '经理', '营销专员', '方向']
without_position_suffixs = ['项目', '州', '站', '平台', '业务', '金', '贴']
split_charts = ['(', ')', '【', '】', '（', '）', '/']
merge_charts = ['\(.*\)', '【.*】', '（.*）']
delete_position_suffixs = ['实习生', '高级', '规划', '资深', '中国移动', '方向', '届', '校招']

def get_position_types(position_data_items):
    
    position_data_items_ = [re.sub(r'\.\.\.', '', item).lower() for item in position_data_items]

    for split_chart in split_charts:
        pattern = re.compile(f'\{split_chart}')
        position_data_items_ = [re.sub(pattern, '-', item) for item in position_data_items_]

    # position_data_items_ = [re.sub(r'(^\d*$)|(\d*$)', '', item) for item in position_data_items_]
    # position_data_items_ = [re.sub(r'[a-zA-Z0-9]', '', item) for item in position_data_items_]

    position_data_dict = {position_data_items[i]: position_data_items_[i] for i in range(len(position_data_items))}

    for oringin, item in position_data_dict.items():
        # sub_merge_items_ = [re.sub(re.compile(merge), '', item) for merge in merge_charts]
        sub_items_ = item.split('-') + [re.sub(r'\-', '', item)]
        # print(sub_items_)
        sub_items = []
        for position_index, sub_item in enumerate(sub_items_):
            for suffix in without_position_suffixs:
                pattern = re.compile(f'(.*{suffix})$')
                # print(sub_item, pattern, re.findall(pattern, sub_item))
                if len(re.findall(pattern, sub_item)) != 0: continue
                sub_items.append(sub_item)
                break

        if len(sub_items) == 0: continue
        position_flag = False
        for position_index, sub_item in enumerate(sub_items):
            for suffix in with_position_suffixs:
                pattern = re.compile(f'(.*{suffix})')
                if len(re.findall(pattern, sub_item)) == 0: continue
                position_flag = True
                break
            if position_flag: break

        for suffix in delete_position_suffixs:
            temp_sub_item_ = re.sub(re.compile(suffix), '', sub_items[position_index])
            temp_sub_item_ = re.sub(r'(^\d*$)|(\d*$)', '', temp_sub_item_)
            if temp_sub_item_ != '': sub_items[position_index] = temp_sub_item_

        position_data_dict[oringin] = {}
        position_data_dict[oringin]['simplify'] = sub_items[position_index]
        # position_data_dict[oringin]['simplify'] = '#'.join(jieba.cut(sub_items[position_index]))


    with open(POSITION_TYPE_FILE, 'r') as f:
        content = f.read()
    position_type = json.loads(content)
    position_type_ = {}

    def _get_item_infos(type_name, dict_item):
        if isinstance(dict_item, list): 
            position_type_[type_name] = dict_item
        elif isinstance(dict_item, dict):
            for vice_type_name, item in dict_item.items():
                _get_item_infos(type_name + '-' + vice_type_name, item)

    for main_type_name, item in position_type.items():
        _get_item_infos(main_type_name, item)
    
    def _get_position_type(position_name):
        for position_type, items in position_type_.items():
            for item in items:
                # print(position_name, item)
                if len(re.findall(re.compile(item), position_name)) == 0: continue
                return position_type

    # position_data_items = []
    for position_name, item in position_data_dict.items():
        position_type = _get_position_type(item['simplify'])
        position_data_items.append(item['simplify'])
        position_data_dict[position_name]['type'] = position_type

    return position_data_dict