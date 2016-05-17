import shutil
import os
import re
import datetime

from tool import conf, git, msgmerge, get_locale_path, manage, update_backend


locale_path = os.path.join(conf['backend']['path'], 'locale')


def process_project(project, release):
    update_backend(release)
    project_path = os.path.join(conf['translations']['path'], project)
    for filename_ext in os.listdir(project_path):
        if filename_ext.endswith('.po'):
            filename = os.path.splitext(filename_ext)[0]
            part, locale = filename.split('-')
            old_po = os.path.join(get_locale_path(), locale, 'LC_MESSAGES', part+'.po')
            new_po = os.path.join(project_path, filename_ext)
            msgmerge(new_po, old_po)
            shutil.copy(new_po, old_po)

            if part == 'pos':
                if conf['makemessages']:
                    out = manage('po_from_lp -l {} -c'.format(locale))
                    m = re.search("(?<=is converted to )(.*)$", out)
                    if m:
                        git('add {}'.format(m.groups()[0]))
            else:
                git('add {}'.format(old_po))
    msg = "Bug 99999 - {} update translations".format(datetime.date.today())
    if conf['commit']:
        git('commit -m', msg)
        git('push')


def commit():
    os.chdir(conf['backend']['path'])
    for project, release in conf['release'].iteritems():
        process_project(project, release)


if __name__ == "__main__":
    commit()
