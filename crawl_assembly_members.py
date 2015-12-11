"""
https://github.com/teampopong/data-assembly에서 assembly.json 데이터를 가져오고
popong api 호출을 위한 popong_idx, 국회 idx, 참여연대 idx를 추가해서
'assembly_members.json'으로 저장
"""
import json
import re
import requests
import path_config

from datetime import datetime

assembly_idx_regex = re.compile(r'dept_cd=([0-9]+)')
open_assembly_idx_regex = re.compile(r'member_seq=([0-9]+)')


def find_popong_idx(name, birthday):
    url = 'http://api.popong.com/v0.1/person/search?q=%s&api_key=test' % name
    birthday_str = birthday.strftime('%Y-%m-%d')
    result = json.loads(requests.get(url).text)
    items = result['items']
    if len(items) == 1:
        return items[0]['id']
    return next((x['id'] for x in items if x['birthday'] == birthday_str), None)


def find_assembly_idx(popong_data_dump, name, birthday):
    birthday_str = birthday.strftime('%Y-%m-%d')
    item = next((x for x in popong_data_dump if x[
                'name_kr'] == name and x['birth'] == birthday_str), None)
    if item is None:
        return None
    return int(assembly_idx_regex.search(item['url']).group(1))


def find_open_assembly_idx(name, birthday):
    url = 'http://watch.peoplepower21.org/New/search.php'
    form_data = {'mname': name}  # birthday isn't used yet
    result = requests.post(url, data=form_data).text
    return int(open_assembly_idx_regex.search(result).group(1))


def append_additional_idxs(popong_data_dump):
    result_dataset = []
    count = len(popong_data_dump)
    i = 0
    for member in popong_data_dump:
        name = member['name_kr']
        birthday = member['birth']
        birthday_date = datetime.strptime(birthday, '%Y-%m-%d').date()

        popong_idx = find_popong_idx(name, birthday_date)
        assembly_idx = find_assembly_idx(popong_data_dump, name, birthday_date)
        open_assembly_idx = find_open_assembly_idx(name, birthday_date)

        result_data = member.copy()
        result_data['popong_idx'] = popong_idx
        result_data['assembly_idx'] = assembly_idx
        result_data['idx'] = open_assembly_idx  # primary idx

        result_dataset.append(result_data)

        i += 1
        print('%d of %d processed.' % (i, count))
    return result_dataset


def fetch_popong_data_dump():
    res = requests.get('https://github.com/teampopong/data-assembly/raw/master/assembly.json')
    res.encoding = 'utf-8'
    return res.json()


def run():
    path_config.create_dirs(path_config.get_container_dir_path())

    popong_data_dump = fetch_popong_data_dump()
    assembly_members_data = append_additional_idxs(popong_data_dump)

    dump_file_path = path_config.get_single_file_path('assembly_members.json')

    with open(dump_file_path, 'w', encoding='utf-8') as out_file:
        json.dump(assembly_members_data, out_file, ensure_ascii=True)
    print('complete')


if __name__ == '__main__':
    run()
