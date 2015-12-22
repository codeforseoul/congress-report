from git import Repo, Actor
import os
import logging
import distutils.core
import datetime


logging.basicConfig(format='[%(asctime)s] %(levelname)s : %(message)s', level=logging.INFO)

ORIGIN_URI = 'git@github.com:codeforseoul/data.git'
REPO_DIR = 'git_dump_repo'
REPO_DATA_DIR = 'congress-report'
DATA_DIR = 'data'


def init_and_pull_repo():
    logging.info('init_repo')

    if not os.path.exists(REPO_DIR):
        Repo.clone_from(ORIGIN_URI, REPO_DIR, branch='master')
        logging.info('git repository cloned')
        return

    repo = Repo.init(REPO_DIR)
    repo.remotes.origin.pull()
    logging.info('pulled')


def update_repo_data():
    logging.info('update repo from local')

    repo_data_path = os.path.join(REPO_DIR, REPO_DATA_DIR)
    distutils.dir_util.copy_tree(DATA_DIR, repo_data_path)


def push_to_origin():
    repo = Repo.init(REPO_DIR)
    repo.index.add([REPO_DATA_DIR])

    changed_count = len(repo.index.diff('HEAD'))

    if (changed_count <= 0):
        logging.info('no changes detected')
        return

    date = datetime.datetime.now().ctime()
    author = Actor('git_dump', 'monster@teamappetizer.com')
    repo.index.commit('git_dump: congress-report %s' % date, author=author)

    logging.info('commited: %d files changed' % changed_count)

    repo.remotes.origin.push()
    logging.info('pushed to origin')


def dump():
    init_and_pull_repo()
    update_repo_data()
    push_to_origin()


if __name__ == '__main__':
    dump()
