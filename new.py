
#-*- coding: UTF-8 -*-
from bs4 import BeautifulSoup
import requests
import datetime
import time
import os
import json

ASSEMBLY_LIST_URL = "http://watch.peoplepower21.org/New/search.php";

#attending information for main-meeting 
#http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_mAttend.php
ATTENDING_MAIN_MEETING = "http://watch.peoplepower21.org/New/cm_info_act_mAttend.php?";

#vote for main meeting 
#http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_mVote.php
VOTE_MAIN_MEETING = "http://watch.peoplepower21.org/New/cm_info_act_mAttend.php?";

#apply law list
#http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_law.php
LAW_LIST = "http://watch.peoplepower21.org/New/cm_info_act_law.php?";

#attending information for sub-meeting
#http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_sAttend.php
ATTEND_SUB_MEETING = "http://watch.peoplepower21.org/New/cm_info_act_sAttend.php?";

#temporary value
CRAWILING_THRESHOLD = 100;

#save result file path
RESULT_PATH = "assembly";


#str_time : ex) 2015-07-15
def convertStrTimeToLong(strTime):
	d = datetime.datetime.strptime(strTime,'%Y-%m-%d');
	return long(time.mktime(d.timetuple())) * 1000

def refreshAttedingInfoMainMeeting(recentDate, assemblyId):
	results = [];

	for pageNum in xrange(1, CRAWILING_THRESHOLD):

		url = ATTENDING_MAIN_MEETING + "member_seq=" + str(assemblyId) + "&page=" + str(pageNum);
		r = requests.get(url);
		r.encoding = 'UTF-8'
		soup = BeautifulSoup(r.text.encode('UTF-8'),'html.parser')
		targetTrs = soup.findAll('tr',attrs={'bgcolor':'#FFFFFF'})

		for targetTr in targetTrs:
		 	tds = targetTr.findAll('td');
		 	if len(tds) == 3 :
 				result = dict();
		 		result['date_str'] = tds[0].text.encode('UTF-8').strip()
		 		result['date'] = convertStrTimeToLong(result['date_str'])
		 		result['number'] = tds[1].text.encode('UTF-8')
		 		result['attend'] = tds[2].text.encode('UTF-8')

				if recentDate < result['date']:
					results.append(result);
				else:
					return results;

	return results;	


def refreshAttedingInfoSubMeeting(recentDate, assemblyId):
	results = [];

	for pageNum in xrange(1, CRAWILING_THRESHOLD):

		url = ATTEND_SUB_MEETING + "member_seq=" + str(assemblyId) + "&page=" + str(pageNum);
		r = requests.get(url);
		r.encoding = 'UTF-8'
		soup = BeautifulSoup(r.text.encode('UTF-8'),'html.parser')
		targetTrs = soup.findAll('tr',attrs={'bgcolor':'#FFFFFF'})

		for targetTr in targetTrs:
		 	tds = targetTr.findAll('td');
		 	if len(tds) == 4 :
 				result = dict();
		 		result['date_str'] = tds[0].text.encode('UTF-8').strip()
		 		result['date'] = convertStrTimeToLong(result['date_str'])
		 		result['number'] = tds[1].text.encode('UTF-8')
		 		result['name'] = tds[2].text.encode('UTF-8')
		 		result['attend'] = tds[3].text.encode('UTF-8')

				if recentDate < result['date']:
					results.append(result);
				else:
					return results;

	return results;	

def extractTime(json):
	try:
		return int(json['date']);
	except KeyError:
		return 0;

def updateToDateAssemblyFile(assemblyId, mAttends, sAttends):
	filename = RESULT_PATH+"/"+str(assemblyId);
	assemblyFile = False;
	assemblyData = dict();
	if os.path.isfile(filename):
		with open(filename, 'r') as assemblyFile:
			assemblyData = json.loads(assemblyFile.read());
	else:
		assemblyData['assembly_id'] = assemblyId;
		assemblyData['main_attend'] = [];
		assemblyData['sub_attend'] = [];

	with open(filename, 'w') as assemblyFile:
		for mAttend in mAttends:
			assemblyData['main_attend'].append(mAttend);

		for sAttend in sAttends:
			assemblyData['sub_attend'].append(sAttend);

		assemblyData['main_attend'] = sorted(assemblyData['main_attend'], key=lambda k: k.get('date', 0), reverse=True);				
		assemblyData['sub_attend'] = sorted(assemblyData['sub_attend'], key=lambda k: k.get('date', 0), reverse=True);				
	
		json.dump(assemblyData, assemblyFile);		

def getRecentAssemblyData(assemblyId):
	recent = dict();
	filename = RESULT_PATH+"/"+str(assemblyId);
	assemblyData = False;
	if os.path.isfile(filename):
		with open(filename, 'r') as assemblyFile:
			assemblyData = json.loads(assemblyFile.read());

	recent['main_attend'] = 0;
	recent['sub_attend'] = 0;

	if assemblyData:
		if len(assemblyData['main_attend']) > 0:
			recent['main_attend'] = assemblyData['main_attend'][0]['date'];		
		if len(assemblyData['sub_attend']) > 0:
			recent['sub_attend'] = assemblyData['sub_attend'][0]['date'];				

	return recent;

def getAllAssemblyId():
	assemblyIdList = [];

	url = ASSEMBLY_LIST_URL;
	r = requests.get(url);
	r.encoding = 'UTF-8'
	soup = BeautifulSoup(r.text.encode('UTF-8'),'html.parser')
	
	assemblyTags = soup.findAll('a',{"href": lambda L: L and L.startswith("cm_info.php?member_seq=")});

	for assemblyTag in assemblyTags:
		href = assemblyTag['href'];
		startIdx = href.find('member_seq=')+len('member_seq=');
		assemblyIdList.append(int(href[startIdx:])) 
	
	return assemblyIdList;

def main():
	if not os.path.exists(RESULT_PATH):
		os.makedirs(RESULT_PATH)


	assemblyIdList = getAllAssemblyId();
	for assemblyId in assemblyIdList:

		recentDates = getRecentAssemblyData(assemblyId);

		mAttends = refreshAttedingInfoMainMeeting(recentDates['main_attend'], assemblyId);
		sAttends = refreshAttedingInfoSubMeeting(recentDates['sub_attend'], assemblyId);

		updateToDateAssemblyFile(assemblyId, mAttends, sAttends);

if __name__ == '__main__':
	main();