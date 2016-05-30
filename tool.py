import os
import yaml
import subprocess
from os import path

from redis import Redis


def get_conf():
    with open(path.join(path.dirname(path.realpath(__file__)), 'conf.yaml'), 'r') as conf_file:
        try:
            return yaml.load(conf_file)
        except yaml.YAMLError as exc:
            print(exc)
conf = get_conf()


def get_locale_path():
    return path.join(conf['backend']['path'], 'locale')


def git(command, msg=None):
    command_seq = ['git'] + command.split(' ')
    if msg:
        command_seq += [msg]
    subprocess.call(command_seq)


def pootle(command):
    if conf['pootle']['enable']:
        subprocess.call([conf['pootle']['bin']] + command.split(' '))


def msgmerge(new, old):
    subprocess.call([conf['msgmerge'], '-U', new, old])


def manage(command):
    return subprocess.check_output([conf['backend']['bin'], 'manage.py'] + command.split(' '))


def get_loc_list(locale_path):
    return [l for l in os.listdir(locale_path) if not l.startswith('.')]


def update_backend(release):
    git('stash')
    git('checkout {}'.format(release))
    git('pull')
    if conf['makemessages']:
        langs = conf['languages'] if conf['languages'] else get_loc_list(get_locale_path())
        makemessages = "makemessages -l {} {} --no-wrap --no-default-ignore --symlinks"
        for l in langs:
            manage(makemessages.format(l, '-e html,txt,py,htm,ejs'))   # for django files
            manage(makemessages.format(l, '-d djangojs'))              # for js files.
            try:
                manage('po_from_lp -f -l {}'.format(l))                # for pos files
            except subprocess.CalledProcessError, ex:
                print "Can't generate pos file!"
        print manage('compilemessages')
        print manage('compilejsi18n')


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