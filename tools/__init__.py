import os
import polib
import json
import hashlib
import yamlconfig
import shutil

from collections import defaultdict
from os import path, makedirs
from itertools import product
from redis import Redis
from datetime import datetime


conf = yamlconfig.Configs().common_conf


def translations_md5(po_path, pos=False):
    pofile = polib.pofile(po_path)
    msg_id = 'msgctxt' if pos else 'msgid'
    translations = {entry.__getattribute__(msg_id): entry.msgstr for entry in pofile if not entry.obsolete}
    return hashlib.md5(json.dumps(translations, sort_keys=True).encode('utf-8')).hexdigest()


# Generation all possible pairs for split settings (path, release, language)
def convert_split_confs():
    result = defaultdict(list)
    for name, settings in conf['split'].items():
        for ls in product(settings['parts'], settings['languages'], settings['release']):
            result['-'.join(ls)].append(name)
    return result


def get_locale_path(locale=None):
    lpath = path.join(conf['backend']['path'], 'locale')
    if locale:
        lpath = path.join(lpath, locale, 'LC_MESSAGES')
    return lpath


def get_loc_list():
    locale_path = get_locale_path()
    return [l for l in os.listdir(locale_path) if not l.startswith('.')]


def remove_pyc_files(path=None):
    path = path or conf['backend']['path']
    for root, dirs, files in os.walk(path):
        for item in files:
            if item.endswith(".pyc"):
                os.remove(os.path.join(root, item))


def backup_translations():
    if conf['translations']['backup']['enable']:
        name_backup = datetime.now().isoformat()
        makedirs(name_backup)
        shutil.copytree(conf['translations']['path'], path.join(conf['translations']['backup']['path'], name_backup))


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


def job_to_dict(job):
    exclude_args = ['_args', '_data', '_dependency_id', '_func_name', '_instance', '_kwargs',
                    'connection']
    result = {}
    for k, v in job.__dict__.items():
        if k not in exclude_args:
            if k.startswith('_'):
                k = k[1:]
            if isinstance(v, datetime):
                v = v.strftime("%B %d, %Y, %H:%M")
            result[k] = v
    return result
