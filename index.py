#-*- coding: UTF-8 -*-
from bs4 import BeautifulSoup
import requests
import json
import re
import codecs
import requests
import os
import datetime
import time
import glob

attend_meta = dict()
attend_meta['result_dir'] = 'result';
attend_meta['crawling_list_url'] = 'http://watch.peoplepower21.org/New/c_monitor_attend.php?page=';
attend_meta['crawling_attend_url'] = 'http://watch.peoplepower21.org/New/c_monitor_attend_detail.php?meeting_seq=';
attend_meta['assembly_id_src'] = ''
attend_meta['target_id_set'] = [];

#temporary value
CRAWILING_THRESHOLD = 100;

#???? what is best way to define model in py ...
def get_recent_meeting_inform():
	recent_meeting = dict();
	recent_meeting['date_str'] = recent_meeting['date'] = recent_meeting['id'] = recent_meeting['summary'] = recent_meeting['content_url'] = None;

	r = requests.get(attend_meta['crawling_list_url']+'1')
	soup = BeautifulSoup(r.text,'html.parser')
	targetTrs = soup.findAll('tr',attrs={'bgcolor':'#FFFFFF'})

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

	r = requests.get(attend_meta['crawling_list_url']+str(page_num))
	soup = BeautifulSoup(r.text,'html.parser')
	targetTrs = soup.findAll('tr',attrs={'bgcolor':'#FFFFFF'})

	for targetTr in targetTrs :
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
	for path in glob.glob(attend_meta['result_dir']+"/*"):
		date = path.replace(attend_meta['result_dir']+"/",'')
		date = convert_str_time_to_int(date);
		
		recent_crawling_date = recent_crawling_date if recent_crawling_date else date 
		
		if(recent_crawling_date < date):
			recent_crawling_date = date; 

	return recent_crawling_date;

def get_target_meetings(crawling_start_date):
	target_meetings = []
	
	for page_num in range(1,CRAWILING_THRESHOLD):
		meetings = get_meetings_by_page_num(page_num)

		if not meetings :
			break;

		if(crawling_start_date<meetings[0]['date']):
			for meeting in meetings :
				target_meetings.append(meeting)
		else:
			break;
	return target_meetings;

def crawling_meeting_content(meeting_meta):

	meeting_inform = dict(meta={},data=[]);
	for key in meeting_meta :
		meeting_inform['meta'][key] = meeting_meta[key]

	cotent_url = meeting_inform['meta']['content_url'];
	r = requests.get(cotent_url)
	soup = BeautifulSoup(r.text,'html.parser')
	
	tables = soup.findAll('table',attrs={'cellspacing':'0','border':'0','width':'750'})	

	if len(tables) == 3:
		lis = tables[2].findAll('li')
		attend_data = dict();
		for li in lis :
			type_text = li.find('b').text
			attend_data['type_name'] = type_text[:type_text.find(' ')]
			attend_data['assemblies'] = [];
			assembly_links = li.find('table').findAll('a')
			for assembly_link in assembly_links :
				href = assembly_link['href'];

				assembly = dict()
				id_start_idx = href.find('member_seq=')+len('member_seq=');
				id_end_idx = href.find('&', id_start_idx);
				
				assembly['id'] = href[id_start_idx:id_end_idx] 
				assembly['name'] = assembly_link.text
				assembly['link'] = href
				attend_data['assemblies'].append(assembly)
		meeting_inform['data'].append(attend_data)

		with open(attend_meta['result_dir']+"/"+meeting_inform['meta']['date_str'],'w') as outfile:
			 json.dump(meeting_inform,outfile)


def crawling_attend():
	if not os.path.exists(attend_meta['result_dir']):
		os.makedirs(attend_meta['result_dir'])

	recent_crawling_date = get_recent_crawling_history_date()
	recent_meeting_date =get_recent_meeting_inform()['date']

	#do crawling
	if(recent_crawling_date < recent_meeting_date):	
		meetings = get_target_meetings(recent_crawling_date)		
		for m in meetings:
			crawling_meeting_content(m)


def get_assembly_by_id(assembly_id):
	page = 1

	assembly_attend = {}
	assembly_attend['id'] = assembly_id;
	assembly_attend['history'] = []

	while(1):
		r = requests.get(attend_meta['crawling_url']+str(assembly_id)+"&page="+str(page))
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

		with open(attend_meta['result_dir']+'/'+str(assembly_id),'w') as outfile:
			json.dump(assembly_attend,outfile)		


def main():
	crawling_attend();

if __name__ == '__main__':
	main()
