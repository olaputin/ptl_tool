import shutil
import os
import re
import datetime
import tool
from rq.decorators import job
from command import Command
from tool import conf, get_locale_path


class Commit(Command):

    def __init__(self):
        super(Commit, self).__init__()

    # @job('commit', connection=redis_connection())
    def execute(self):
        self.logger.info("Start commit processing")
        os.chdir(conf['backend']['path'])
        for project in conf['release']['enable']:
            release = conf['release']['available'][project]
            tool.remove_pyc_files(conf['backend']['path'])
            self.git('clean -f')
            self.process_project(project, release)
        self.set_last_execute()
        self.logger.info("Finish commit processing")

    def process_project(self, project, release):
        self.update_backend(release)
        project_path = os.path.join(conf['translations']['path'], project)
        for filename_ext in os.listdir(project_path):
            if filename_ext.endswith('.po'):
                filename = os.path.splitext(filename_ext)[0]
                part, locale = filename.split('-')
                if locale in conf['languages']:
                    old_po = os.path.join(get_locale_path(locale), part+'.po')
                    new_po = os.path.join(project_path, filename_ext)
                    self.msgmerge(new_po, old_po)
                    shutil.copy(new_po, old_po)

                    if part == 'pos':
                        out = self.manage('po_from_lp -l {} -c'.format(locale))
                        m = re.search("(?<=is converted to )(.*)$", out)
                        if m:
                            self.git('add {}'.format(m.groups()[0]))
                    else:
                        self.git('add {}'.format(old_po))
        msg = "Bug 1194 - {} update translations".format(datetime.date.today())
        if conf['commit']:
            self.git('commit -m', msg)
            self.git('push')


if __name__ == "__main__":
    cmd = Commit()
    cmd.execute()
