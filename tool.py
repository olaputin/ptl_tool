
import os
import yamlconfig
import subprocess
from os import path

from redis import Redis


conf = yamlconfig.Configs().common_conf


def get_locale_path(locale=None):
    lpath = path.join(conf['backend']['path'], 'locale')
    if locale:
        lpath = path.join(lpath, locale, 'LC_MESSAGES')
    return lpath


def get_loc_list():
    locale_path = get_locale_path()
    return [l for l in os.listdir(locale_path) if not l.startswith('.')]



def remove_pyc_files(path):
    for root, dirs, files in os.walk(path):
        for item in files:
            if item.endswith(".pyc"):
                os.remove(os.path.join(root, item))


def set_last_execute(cmd, time_of_execute):
    redis_connection().set('ptl:{}:last_exec'.format(cmd), time_of_execute)


def get_last_execute(cmd):
    return redis_connection().get('ptl:{}:last_exec'.format(cmd))


def redis_connection():
    return Redis()


def redis_get_wip(queue_name):
    name = "rq:wip:{}".format(queue_name)
    redis = redis_connection()
    return redis.zrange(name, 0, -1)


def redis_get_queue(queue_name):
    name = "rq:queue:{}".format(queue_name)
    redis = redis_connection()
    return redis.lrange(name, 0, -1)


def make_task(callback):
    from rq import Queue
    redis_conn = Redis()
    q = Queue(connection=redis_conn)
    job = q.enqueue(callback)
    return job.id