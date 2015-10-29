# watch.peoplepower21.org
import json
import os
import re
import requests

from bs4 import BeautifulSoup

DUMP_DIR = 'plenary_session_results'

go_to_page_regex = re.compile(r'javascript:goToPage\((\d+)\);')
mbill_regex = re.compile(r'mbill=(\d+)"')
member_seq_regex = re.compile(r'member_seq=(\d+)&')

def _compute_has_next(html, cur_page):
    has_next = False
    go_to_page_matches = go_to_page_regex.findall(html)
    for x in go_to_page_matches:
        has_next |= (int(x) > cur_page)
    return has_next


def fetch_sessions(page):
    """
    {
        'sessions': [{
            'bill': 9373,
            '처리날짜': '2015-09-08',
            '회차': '제337회 04차',
            '의안명': '2014회계연도 결산',
            '결과': '의안가결'
        }, ...],
        'has_next': true
    }
    """
    url = 'http://watch.peoplepower21.org/New/monitor_voteresult.php?page=%d' % page
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    has_next = _compute_has_next(res.text, page)

    _table = soup.find('td', attrs={'bgcolor': '#AFAFAF'})
    _inner_table = _table.find('table')
    _trs = _inner_table.find_all('tr')
    _entry_trs = _trs[1:-2]

    sessions = []
    for entry_tr in _entry_trs:
        _entry_tds = entry_tr.find_all('td')
        _bill = int(mbill_regex.search(str(entry_tr)).group(1))
        _date = _entry_tds[0].string
        _index = _entry_tds[1].string
        _subject = _entry_tds[2].find('a').string.strip()
        _result = _entry_tds[3].string
        sessions.append({
                'bill': _bill,
                '처리날짜': _date,
                '회차': _index,
                '의안명': _subject,
                '결과': _result
            })

    return {
        'sessions': sessions,
        'has_next': has_next
    }


def fetch_session_vote_results(session_bill):
    url = 'http://watch.peoplepower21.org/New/c_monitor_voteresult_detail.php?mbill=%d' % session_bill
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    _result_trs = soup.find_all('tr', attrs={'bgcolor': '#FFFFFF'})

    results = []
    for result_tr in _result_trs:
        _tds = result_tr.find_all('td')
        if len(_tds) != 2:
            continue

        _type = _tds[0].contents[0].replace('*', '')
        _members = list(map(lambda x: int(x), member_seq_regex.findall(str(_tds[1]))))
        results.append({
                'type': _type,
                'member_idxs': _members
            })

    return results


def _get_dump_file_path(session_bill, session_date):
    return '%s/%s.%d.json' % (DUMP_DIR, session_date, session_bill)


def crawl_all_sessions():
    if not os.path.exists(DUMP_DIR):
        os.makedirs(DUMP_DIR)

    page_no = 1
    while True:
        sessions_ret = fetch_sessions(page_no)
        sessions = sessions_ret['sessions']

        for session in sessions:
            session_bill = session['bill']
            session_date = session['처리날짜']
            session_index = session['회차']
            session_subject = session['의안명']
            session_result = session['결과']

            dump_file_path = _get_dump_file_path(session_bill, session_date)
            if os.path.exists(dump_file_path):
                print('%s.%d skip' % (session_date, session_bill))
                continue

            print('%s.%d %s start' % (session_date, session_bill, session_subject))

            session_vote_results = fetch_session_vote_results(session_bill)

            # 추가 정보
            session_details = {
                'bill': session_bill,
                '처리날짜': session_date,
                '회차': session_index,
                '의안명': session_subject,
                '결과': session_result,
                'vote_results': session_vote_results
            }

            with open(dump_file_path, 'w') as out_file:
                json.dump(session_details, out_file, ensure_ascii=False, sort_keys=False, indent=4)

            print('%s out' % dump_file_path)

        if sessions_ret['has_next'] is False:
            break
        page_no += 1


if __name__ == '__main__':
    crawl_all_sessions()
