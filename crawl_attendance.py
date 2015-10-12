import datetime
import glob
import json
import os
import requests
import sys
import time

from bs4 import BeautifulSoup

attend_meta = dict()
attend_meta['result_dir'] = 'result';
attend_meta['crawling_list_url'] = 'http://watch.peoplepower21.org/New/c_monitor_attend.php?page=';
attend_meta['crawling_attend_url'] = 'http://watch.peoplepower21.org/New/c_monitor_attend_detail.php?meeting_seq=';
attend_meta['assembly_list_url'] = 'http://watch.peoplepower21.org/New/search.php';
attend_meta['target_id_set'] = [];

#temporary value
CRAWILING_THRESHOLD = 100;

#???? what is best way to define model in py ...
def get_recent_meeting_inform():
    recent_meeting = dict();
    recent_meeting['date_str'] = recent_meeting['date'] = recent_meeting['id'] = recent_meeting['summary'] = recent_meeting['content_url'] = None;

    r = requests.get(attend_meta['crawling_list_url'] + '1')
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')
    targetTrs = soup.findAll('tr', attrs = {'bgcolor': '#FFFFFF'})

    if len(targetTrs) > 0 :
        targetTr = targetTrs[0]
        tds = targetTr.findAll('td');
        if len(tds) == 3 :
            recent_meeting['date_str'] = tds[0].text.strip()
            recent_meeting['date'] = convert_str_time_to_int(recent_meeting['date_str'])
            recent_meeting['id'] = tds[1].text
            recent_meeting['summary'] = tds[2].text
            recent_meeting['content_url'] = tds[0].find('a')['href']

    return recent_meeting;



def get_meetings_by_page_num(page_num):
    meettings = [];

    r = requests.get(attend_meta['crawling_list_url'] + str(page_num))
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')
    targetTrs = soup.findAll('tr', attrs = {'bgcolor': '#FFFFFF'})

    for targetTr in targetTrs:
        tds = targetTr.findAll('td');
        if len(tds) == 3 :
            recent_meeting = dict();
            recent_meeting['date_str'] = tds[0].text.strip()
            recent_meeting['date'] = convert_str_time_to_int(recent_meeting['date_str'])
            recent_meeting['id'] = tds[1].text
            recent_meeting['summary'] = tds[2].text
            recent_meeting['content_url'] = tds[0].find('a')['href']

            meettings.append(recent_meeting);

    return meettings;

#str_time : ex) 2015-07-15
def convert_str_time_to_int(str_time):
    d = datetime.datetime.strptime(str_time,'%Y-%m-%d');
    return int(time.mktime(d.timetuple())) * 1000

def get_recent_crawling_history_date():
    recent_crawling_date = 0;

    #to update detact date-format
    for path in glob.glob(attend_meta['result_dir'] + '/*'):
        date = path.replace(attend_meta['result_dir'] + '/', '').replace('.json', '')
        date = convert_str_time_to_int(date)

        recent_crawling_date = recent_crawling_date if recent_crawling_date else date

        if (recent_crawling_date < date):
            recent_crawling_date = date

    return recent_crawling_date

def get_target_meetings(crawling_start_date):
    target_meetings = []

    for page_num in range(1,CRAWILING_THRESHOLD):
        meetings = get_meetings_by_page_num(page_num)

        if not meetings :
            break;

        if(crawling_start_date < meetings[0]['date']):
            for meeting in meetings:
                target_meetings.append(meeting)
        else:
            break;
    return target_meetings;

def crawling_meeting_content(meeting_meta):
    meeting_inform = dict(meta = {}, data = []);
    for key in meeting_meta:
        meeting_inform['meta'][key] = meeting_meta[key]

    content_url = meeting_inform['meta']['content_url'];
    r = requests.get(content_url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    tables = soup.findAll('table', attrs = {'cellspacing': '0', 'border': '0', 'width': '750'})

    if len(tables) == 3:
        lis = tables[2].findAll('li')
        for li in lis :
            attend_data = dict();
            type_text = li.find('b').text
            attend_data['type_name'] = type_text[:type_text.find(' ')]
            attend_data['assemblies'] = [];
            assembly_links = li.find('table').findAll('a')
            for assembly_link in assembly_links :
                href = assembly_link['href']

                assembly = dict()
                id_start_idx = href.find('member_seq=') + len('member_seq=')
                id_end_idx = href.find('&', id_start_idx);

                assembly['id'] = href[id_start_idx:id_end_idx]
                assembly['name'] = str(assembly_link.text)
                assembly['link'] = href
                attend_data['assemblies'].append(assembly)
            meeting_inform['data'].append(attend_data)

        with open(attend_meta['result_dir']+ "/" +meeting_inform['meta']['date_str'] + ".json",'w') as outfile:
            json.dump(meeting_inform, outfile, ensure_ascii=False)


def crawling_attend():
    print('crawling_attend: start')

    if not os.path.exists(attend_meta['result_dir']):
        os.makedirs(attend_meta['result_dir'])

    recent_crawling_date = get_recent_crawling_history_date()
    recent_meeting_date =get_recent_meeting_inform()['date']

    #do crawling
    if(recent_crawling_date < recent_meeting_date):
        meetings = get_target_meetings(recent_crawling_date)
        for m in meetings:
            print(m)
            crawling_meeting_content(m)

    print('crawling_attend: complete')


def get_assembly_by_id(assembly_id):
    page = 1

    assembly_attend = {}
    assembly_attend['id'] = assembly_id;
    assembly_attend['history'] = []

    while(1):
        r = requests.get(attend_meta['crawling_url']+str(assembly_id)+"&page="+str(page))
        r.encoding = 'utf-8'
        page = page + 1;
        soup = BeautifulSoup(r.text,'html.parser')
        targetTable = soup.find('table',attrs={'cellpadding':'5','cellspacing':'1','border':'0','width':'650'})

        trs = targetTable.findAll('tr',attrs={'align':'center', 'bgcolor':'#FFFFFF'})

        if(len(trs) > 0):
            for tr in trs:
                tds = tr.findAll('td')
                date_str = tds[0].text
                count_str = tds[1].text
                attend_value = tds[2].text

                assembly_attend['history'].append(dict(date_str=date_str,count_str=count_str,attend_value=attend_value))
        else:
            break;

        with open(attend_meta['result_dir']+ "/" + str(assembly_id) + ".json",'w') as outfile:
            json.dump(assembly_attend, outfile, ensure_ascii=False)



def get_all_of_assemblies():
    assemblies = dict()

    url = attend_meta['assembly_list_url']
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text,'html.parser')

    expectedAssemblyLinks = soup.findAll('a')
    for expectedAssemblyLink in expectedAssemblyLinks:
        href = expectedAssemblyLink['href']
        if 'member_seq=' in href:
            assembly = dict()
            id_start_idx = href.find('member_seq=')+len('member_seq=')
            assembly_text = expectedAssemblyLink.text
            assembly_title = expectedAssemblyLink['title']

            assembly_id = int(href[id_start_idx:])
            assembly_name = assembly_text[:assembly_text.find(' ')].strip()
            assembly_party = assembly_title[:assembly_title.find('-')].strip()

            assemblies[assembly_id] = dict({
                'name' : assembly_name,
                'party' : assembly_party
                });

    return assemblies;

#this must called after crawling_attend()
def get_all_of_meet_dates():
    dates = dict()

    for path in glob.glob(attend_meta['result_dir']+"/*"):
        date_str = path.replace(attend_meta['result_dir']+"/",'').replace('.json', '')
        date = convert_str_time_to_int(date_str);
        dates[date_str] = date;

    return dates;

def get_attend_result(meet_date, src_assembly):

    result = '';
    with open(attend_meta['result_dir']+ "/" + meet_date + ".json",'r') as json_data:
        meet_data = json.load(json_data);
        for attend_data in meet_data['data']:
            type_name = attend_data['type_name'];
            assemblies = attend_data['assemblies'];
            for assembly in assemblies:
                assembly_id = int(assembly['id']);

                #??? 'if assembly_id is src_assembly' why not working....
                if assembly_id - src_assembly is 0:
                    result = type_name;
                    break;

    return result;

def analyze_assemblies_attend():
    results = dict({
            "results" : []
            })
    meet_dates = get_all_of_meet_dates();
    assemblies = get_all_of_assemblies();

    assembies_attend = dict()

    for assembly_id in assemblies:
        assembies_attend[assembly_id] = dict({
            'date_raw' : dict(),
            'meet_count': 0,
            'attend_count': 0,
            'attend_percent': 0.0,
            'attend_set': dict()
        });


    for assembly_id in assembies_attend:
        for meet_date in meet_dates:
            assembies_attend[assembly_id]['date_raw'][meet_date] = get_attend_result(meet_date,assembly_id)


    for assembly_id in assembies_attend:
        assembly_attend = assembies_attend[assembly_id];
        attend_count = 0;
        meet_count = 0;
        date_raw = assembly_attend['date_raw'];
        attend_set = assembly_attend['attend_set'];
        for meet_date in date_raw:
            attend_type = date_raw[meet_date];
            if len(attend_type) > 0:
                meet_count+=1;

                if attend_type not in attend_set:
                    attend_set[attend_type] = [];

                attend_set[attend_type].append(meet_dates[meet_date])

        attend_count = 0;
        attend_percent = 0;
        if str('출석') in attend_set:
            attend_count = len(attend_set[str('출석')]);
            attend_percent = float(attend_count)/float(meet_count)

        assembly_attend['meet_count'] = meet_count;
        assembly_attend['attend_count'] = attend_count;
        assembly_attend['attend_percent'] = attend_percent;

        result_assembly = dict({
            "assembly" : assemblies[assembly_id],
            "attend_inform" : assembly_attend
            });
        result_assembly['assembly']['id'] = assembly_id;
        results['results'].append(result_assembly);


    results['results'] = sorted(results['results'], key=lambda k: k['attend_inform']['attend_percent'], reverse=True)
    with open('assemblies_attend','w') as outfile:
        json.dump(results, outfile, ensure_ascii=False)

def main():
    crawling_attend()
    analyze_assemblies_attend()

if __name__ == '__main__':
    main()



### important!!!! ###

#r.encoding = 'utf-8'
#
#
#       r = requests.get(cotent_url)
#       r.encoding='utf-8';
#       soup = BeautifulSoup(r.text,'html.parser')

#to read utf-8 encoding file
#
#   once
#       reload(sys)
#       sys.setdefaultencoding('utf-8')
#
#   after
#      txt.decode('utf-8').encode('utf-8')
#
#


