# dir path
import os

CONTAINER_DIR = 'data'


def get_data_dir_path(collection_name):
    return '%s/%s' % (CONTAINER_DIR, collection_name)


def get_container_dir_path():
    return CONTAINER_DIR


def get_single_file_path(collection_name):
    return '%s/%s' % (CONTAINER_DIR, collection_name)


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
