import db_config
import json
import os

from pymongo import MongoClient

import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s : %(message)s', level=logging.INFO)


def dump_files(db, container_dir):
    logging.info('insert_files_to_mongo: begin: %s' % container_dir)

    if not os.path.exists(container_dir):
        logging.warning('insert_files_to_mongo: cancelled: no dir')
        return

    files = os.listdir(container_dir)
    coll = db[container_dir]

    for filename in files:
        file_lower = filename.lower()
        if not file_lower.endswith('.json'):
            continue

        filepath = os.path.join(container_dir, filename)

        # skip if exists
        unique_id = filepath
        has_doc_already = (coll.find_one({'unique_id': unique_id}) != None)
        if has_doc_already:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                doc = json.load(f)
            except:
                logging.error('%s error' % filepath)
                raise

        doc['unique_id'] = unique_id
        coll.insert_one(doc)

        logging.info('%s: %s inserted' % (container_dir, filename))
    logging.info('insert_files_to_mongo: traceout')


def dump_single_file(db, unique_key, filename):
    logging.info('update_file_to_mongo: begin')

    coll_name = filename.lower().replace('.json', '')
    coll = db[coll_name]

    with open(filename, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    for el in doc:
        unique_id = el[unique_key]
        ret = coll.replace_one({unique_key: unique_id}, el, upsert=True)
        logging.info('idx: %d' % unique_id)

    logging.info('update_file_to_mongo: traceout')

def run():
    SINGLE_FILES = ['assembly_people.json']
    DATA_DIRS = ['plenary_session_results', 'attendance_results']

    logging.info('begin mongodump')
    client = MongoClient(db_config.MONGO_URI)
    db = client.congress_report

    for x in DATA_DIRS:
        dump_files(db, x)

    for x in SINGLE_FILES:
        dump_single_file(db, 'idx', x)

    logging.info('complete')


if __name__ == '__main__':
    run()
