"""
매주 월요일 오전 10:00에 crawl_*.py 스크립트를 실행하고, 크롤링된 데이터를 몽고DB에 저장함
"""
import schedule
import time
import os
import sys
from datetime import datetime
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s : %(message)s', level=logging.INFO)

def _run_script(python_file):
    logging.info('[%s] run %s script' % (datetime.now().isoformat(), python_file))
    try:
        mod = __import__(python_file.replace('.py', ''))
        mod.run()
    except Exception as e:
        logging.error('exception occured')
        logging.error(sys.last_traceback)
        logging.error(e)

    logging.info('[%s] done' % (datetime.now().isoformat()))


def run_crawl_scripts():
    # crawl_*.py 파일을 실행함
    crawl_script_files = [x for x in os.listdir('.') if x.startswith('crawl_')]
    for script_file in crawl_script_files:
        _run_script(script_file)
        time.sleep(3)


def execute_crawl_and_backup():
    run_crawl_scripts()
    _run_script('mongo_dump')


def schedule_job():
    logging.info('schedule_job start')

    # run once first
    execute_crawl_and_backup()

    schedule.every().monday.at('10:00').do(execute_crawl_and_backup)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    schedule_job()
