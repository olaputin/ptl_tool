import os
import yaml
import subprocess
from os import path


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
    subprocess.call([get_conf()['msgmerge'], '-U', new, old])


def manage(command):
    return subprocess.check_output([conf['backend']['bin'], 'manage.py'] + command.split(' '))


def get_loc_list(locale_path):
    return [l for l in os.listdir(locale_path) if not l.startswith('.')]


def update_backend(release):
    git('stash')
    git('checkout {}'.format(release))
    # git('pull')
    if conf['makemessages']:
        langs = conf['languages'] if conf['languages'] else get_loc_list(locale_path)
        makemessages = "makemessages -l {} {} --no-wrap --no-default-ignore --symlinks"
        for l in langs:
            manage(makemessages.format(l, '-e html,txt,py,htm,ejs'))   # for django files
            manage(makemessages.format(l, '-d djangojs'))              # for js files.
            manage('po_from_lp -f -l ru')                              # for pos files
