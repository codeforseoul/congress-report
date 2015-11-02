import db_config
import json
import os

from pymongo import MongoClient


def dump_files(db, container_dir):
    print('insert_files_to_mongo: begin: %s' % container_dir)

    if not os.path.exists(container_dir):
        print('insert_files_to_mongo: cancelled: no dir')
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
            doc = json.load(f)

        doc['unique_id'] = unique_id
        coll.insert_one(doc)

        print('%s: %s inserted' % (container_dir, filename))
    print('insert_files_to_mongo: traceout')


def dump_single_file(db, unique_key, filename):
    print('update_file_to_mongo: begin')

    coll_name = filename.lower().replace('.json', '')
    coll = db[coll_name]

    with open(filename, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    for el in doc:
        unique_id = el[unique_key]
        ret = coll.replace_one({unique_key: unique_id}, el, upsert=True)
        print('idx: %d' % unique_id)

    print('update_file_to_mongo: traceout')


SINGLE_FILES = ['assembly_people.json']
DATA_DIRS = ['plenary_session_results', 'attendance_results']

if __name__ == '__main__':
    print('begin')
    client = MongoClient(db_config.MONGO_URI)
    db = client.congress_report

    for x in DATA_DIRS:
        dump_files(db, x)

    for x in SINGLE_FILES:
        dump_single_file(db, 'idx', x)

    print('complete')
