import shutil
import tool
import time

from datetime import datetime
from rq.decorators import job
from tool import conf, git, get_locale_path, pootle, manage, update_backend, get_loc_list, redis_connection
from os import chdir, path, listdir, makedirs


locale_path = get_locale_path()


@job('checkout', connection=redis_connection())
def checkout():
    chdir(conf['backend']['path'])
    for project, release in conf['release'].iteritems():
        tool.remove_pyc_files(conf['backend']['path'])
        git('clean -f')
        update_backend(release)
        process_project(project)
    pootle('update_stores')
    pootle('refresh_stats')

    tool.set_last_execute('checkout', time.mktime(datetime.utcnow().timetuple()))


def process_project(project):
    project_path = path.join(conf['translations']['path'], project)
    if not path.exists(project_path):
        makedirs(project_path)
    locale_list = get_loc_list(locale_path)
    for l in locale_list:
        if conf['languages'] and l not in conf['languages']:
            continue
        copy_locale_files(project_path, l)


def copy_locale_files(project_path, locale):
    print "locale -{}- in progress".format(locale)
    files_dir = path.join(locale_path, locale, 'LC_MESSAGES')
    for f in listdir(files_dir):
        if f.endswith('.po'):
            shutil.copy(path.abspath(path.join(files_dir, f)),
                        path.join(project_path, '{}-{}.po'.format(path.splitext(f)[0],
                                                                     locale)))
            print path.abspath(path.join(files_dir, f))


if __name__ == "__main__":
    checkout()
