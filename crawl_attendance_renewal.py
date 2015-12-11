from bs4 import BeautifulSoup
import requests
import datetime
import time
import os
import json
import path_config

ASSEMBLY_LIST_URL = "http://watch.peoplepower21.org/New/search.php"

# attending information for main-meeting
# http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_mAttend.php
ATTENDING_MAIN_MEETING = "http://watch.peoplepower21.org/New/cm_info_act_mAttend.php?"

# vote for main meeting
# http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_mVote.php
VOTE_MAIN_MEETING = "http://watch.peoplepower21.org/New/cm_info_act_mAttend.php?"

# apply law list
# http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_law.php
LAW_LIST = "http://watch.peoplepower21.org/New/cm_info_act_law.php?"

# attending information for sub-meeting
# http://watch.peoplepower21.org/New/cm_info.php?member_seq=775&info_page=cm_info_act_sAttend.php
ATTEND_SUB_MEETING = "http://watch.peoplepower21.org/New/cm_info_act_sAttend.php?"

# temporary value
CRAWILING_THRESHOLD = 100

# save result file path
RESULT_PATH = path_config.get_data_dir_path('attendance_results')


# str_time : ex) 2015-07-15
def convertStrTimeToLong(strTime):
    d = datetime.datetime.strptime(strTime, '%Y-%m-%d')
    return int(time.mktime(d.timetuple())) * 1000


def refreshAttedingInfoMainMeeting(recentDate, assemblyId):
    results = []

    for pageNum in range(1, CRAWILING_THRESHOLD):
        url = ATTENDING_MAIN_MEETING + "member_seq=" + \
            str(assemblyId) + "&page=" + str(pageNum)
        r = requests.get(url)
        r.encoding = 'UTF-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        targetTrs = soup.findAll('tr', attrs={'bgcolor': '#FFFFFF'})

        for targetTr in targetTrs:
            tds = targetTr.findAll('td')
            if len(tds) == 3:
                result = dict()
                result['date_str'] = tds[0].text.strip()
                result['date'] = convertStrTimeToLong(result['date_str'])
                result['number'] = tds[1].text
                result['attend'] = tds[2].text

                if recentDate < result['date']:
                    results.append(result)
                else:
                    return results

        return results


def refreshAttedingInfoSubMeeting(recentDate, assemblyId):
    results = []

    for pageNum in range(1, CRAWILING_THRESHOLD):
        url = ATTEND_SUB_MEETING + "member_seq=" + \
            str(assemblyId) + "&page=" + str(pageNum)
        r = requests.get(url)
        r.encoding = 'UTF-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        targetTrs = soup.findAll('tr', attrs={'bgcolor': '#FFFFFF'})

        for targetTr in targetTrs:
            tds = targetTr.findAll('td')
            if len(tds) == 4:
                result = dict()
                result['date_str'] = tds[0].text.strip()
                result['date'] = convertStrTimeToLong(result['date_str'])
                result['number'] = tds[1].text
                result['name'] = tds[2].text
                result['attend'] = tds[3].text

                if recentDate < result['date']:
                    results.append(result)
                else:
                    return results

    return results


def extractTime(json):
    try:
        return int(json['date'])
    except KeyError:
        return 0


def updateToDateAssemblyFile(assemblyId, mAttends, sAttends):
    filename = '%s/%s.json' % (RESULT_PATH, str(assemblyId))
    assemblyFile = False
    assemblyData = dict()
    if os.path.isfile(filename):
        with open(filename, 'r') as assemblyFile:
            assemblyData = json.loads(assemblyFile.read())
    else:
        assemblyData['member_idx'] = assemblyId
        assemblyData['main_attend'] = []
        assemblyData['sub_attend'] = []

    with open(filename, 'w') as assemblyFile:
        for mAttend in mAttends:
            assemblyData['main_attend'].append(mAttend)

        for sAttend in sAttends:
            assemblyData['sub_attend'].append(sAttend)

        assemblyData['main_attend'] = sorted(
            assemblyData['main_attend'], key=lambda k: k.get('date', 0), reverse=True)
        assemblyData['sub_attend'] = sorted(
            assemblyData['sub_attend'], key=lambda k: k.get('date', 0), reverse=True)

        json.dump(assemblyData, assemblyFile)


def getRecentAssemblyData(assemblyId):
    recent = dict()
    filename = RESULT_PATH+"/"+str(assemblyId)
    assemblyData = False
    if os.path.isfile(filename):
        with open(filename, 'r') as assemblyFile:
            assemblyData = json.loads(assemblyFile.read())

    recent['main_attend'] = 0
    recent['sub_attend'] = 0

    if assemblyData:
        if len(assemblyData['main_attend']) > 0:
            recent['main_attend'] = assemblyData['main_attend'][0]['date']
        if len(assemblyData['sub_attend']) > 0:
            recent['sub_attend'] = assemblyData['sub_attend'][0]['date']

    return recent


def fetch_members_idxs():
    member_idxs = []

    url = ASSEMBLY_LIST_URL
    r = requests.get(url)
    r.encoding = 'UTF-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    assemblyTags = soup.findAll(
        'a', {"href": lambda L: L and L.startswith("cm_info.php?member_seq=")})

    for assemblyTag in assemblyTags:
        href = assemblyTag['href']
        startIdx = href.find('member_seq=')+len('member_seq=')
        member_idxs.append(int(href[startIdx:]))

    return member_idxs


def run():
    path_config.create_dirs(RESULT_PATH)

    print('begin')
    member_idxs = fetch_members_idxs()
    for member_idx in member_idxs:
        print('getting assembly data, member idx: %d' % member_idx)
        recentDates = getRecentAssemblyData(member_idx)

        mAttends = refreshAttedingInfoMainMeeting(
            recentDates['main_attend'], member_idx)
        sAttends = refreshAttedingInfoSubMeeting(
            recentDates['sub_attend'], member_idx)

        updateToDateAssemblyFile(member_idx, mAttends, sAttends)
        print('complete')
    print('end')

if __name__ == '__main__':
    run()
