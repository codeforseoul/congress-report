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

attend_meta = dict()
attend_meta['result_dir'] = 'result';
attend_meta['crawling_url'] = 'http://watch.peoplepower21.org/New/c_monitor_attend.php?page=';
attend_meta['assembly_id_src'] = ''
attend_meta['target_id_set'] = [];

def init():
	if not os.path.exists(attend_meta['result_dir']):
		os.makedirs(attend_meta['result_dir'])

	r = requests.get(attend_meta['crawling_url']+'1')
	r.encoding = 'UTF-8'
	soup = BeautifulSoup(r.text.encode('UTF-8'),'html.parser')
	targetTable = soup.findAll('table',attrs={'class':'table_head1'})

	if len(targetTable) > 2:
		targetTable = targetTable[2];
		print(targetTable);
#		targetTable = targetTable[2].find('table',attrs={'class':'table_head1'}).find('table').find('tbody')
#		print(targetTable)
#		trs = targetTable.findAll('tr')		

#		print(trs)
#		if(len(trs)>0):
#			recentDate = trs[0].findAll('td')[0].text
#			print(recentDate)
	#file_format
	#[assembly_id]_[recent_date]_[count_id]
#	d = datetime.datetime.strptime(date,'%Y-%m-%d')
#	t = long(time.mktime(d.timetuple())) * 1000;


#	for f in os.listdir(attend_meta['result_dir']):


#	r = requests.get(attend_meta['assembly_id_src']);
#	r.json();


def get_assembly_by_id(assembly_id):
	page = 1

	assembly_attend = {}
	assembly_attend['id'] = assembly_id;
	assembly_attend['history'] = []

	while(1):
		r = requests.get(attend_meta['crawling_url']+str(assembly_id)+"&page="+str(page))
		page = page + 1;
		r.encoding = 'UTF-8'
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
	init();
#	get_assembly_by_id(115)

if __name__ == '__main__':
	main()
