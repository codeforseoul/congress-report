import db_config
import json
import os
import path_config

from datetime import datetime

from pymongo import MongoClient

import logging

logging.basicConfig(
    format='[%(asctime)s] %(levelname)s : %(message)s', level=logging.INFO)

CONTAINER_DIR = path_config.get_container_dir_path()


def dump_data_dir(db, dir_name):
    dir_path = os.path.join(CONTAINER_DIR, dir_name)
    logging.info('insert_files_to_mongo: begin: %s' % dir_path)

    if not os.path.exists(dir_path):
        logging.warning('insert_files_to_mongo: cancelled: no dir')
        return

    files = os.listdir(dir_path)
    coll = db[dir_name]
    skip_count = 0

    for filename in files:
        file_lower = filename.lower()
        if not file_lower.endswith('.json'):
            continue

        file_path = os.path.join(dir_path, filename)
        unique_id = file_path

        cur_version = int(os.path.getmtime(file_path))
        old_doc = coll.find_one({'unique_id': unique_id})

        if old_doc is not None:
            old_version = old_doc['version']
            if old_version == cur_version:
                skip_count += 1
                continue

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                doc = json.load(f)
            except:
                logging.error('%s error' % file_path)
                raise

        doc['unique_id'] = unique_id
        doc['modified'] = datetime.utcnow()
        doc['version'] = cur_version

        coll.replace_one({'unique_id': unique_id}, doc, upsert=True)

        logging.info('%s: %s inserted' % (dir_name, filename))

    logging.info('skip_count: %d' % skip_count)
    logging.info('insert_files_to_mongo: traceout')


def dump_single_file(db, unique_key, filename):
    logging.info('update_file_to_mongo: begin')

    coll_name = filename.lower().replace('.json', '')
    coll = db[coll_name]

    file_path = os.path.join(CONTAINER_DIR, filename)

    with open(file_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    for el in doc:
        unique_id = el[unique_key]
        el['modified'] = datetime.utcnow()
        coll.replace_one({unique_key: unique_id}, el, upsert=True)
        logging.info('idx: %d' % unique_id)

    logging.info('update_file_to_mongo: traceout')


def find_single_files():
    files = []
    for f in os.listdir(CONTAINER_DIR):
        if os.path.isfile(os.path.join(CONTAINER_DIR, f)) and f.endswith('.json'):
            files.append(f)
    return files


def find_data_dirs():
    dirs = []
    for f in os.listdir(CONTAINER_DIR):
        if os.path.isdir(os.path.join(CONTAINER_DIR, f)):
            dirs.append(f)
    return dirs


def run():
    logging.info('begin mongodump')

    single_files = find_single_files()
    data_dirs = find_data_dirs()

    print(single_files)
    print(data_dirs)

    client = MongoClient(db_config.MONGO_URI)
    db = client.congress_report

    for x in single_files:
        dump_single_file(db, 'idx', x)

    for x in data_dirs:
        dump_data_dir(db, x)

    logging.info('complete')


if __name__ == '__main__':
    run()
