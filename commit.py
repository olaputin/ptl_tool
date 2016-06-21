import datetime
import os
import re
import shutil

from command import Command
from tools import conf, get_locale_path, translations_md5, remove_pyc_files
from tools.pofiles import SplitNamePo, OriginNamePo, BackendNamePo, \
    get_full_path, get_filename, get_po_files


class Commit(Command):

    def __init__(self):
        super(Commit, self).__init__()

    # @job('commit', connection=redis_connection())
    def execute(self):
        self.logger.info("Start commit processing")
        os.chdir(conf['backend']['path'])
        for project in conf['release']['enable']:
            release = conf['release']['available'][project]
            remove_pyc_files(conf['backend']['path'])
            self.git('clean -f')
            self.process_project(project, release)
        self.set_last_execute()
        self.logger.info("Finish commit processing")

    def process_project(self, project, release):
        self.update_backend(release)
        project_path = os.path.join(conf['translations']['path'], project)
        changed = []
        for f in get_po_files(project_path, SplitNamePo):
            is_pos = f.part == 'pos'
            if f.locale in conf['languages']:
                old_po = get_full_path(BackendNamePo(get_locale_path(f.locale), f.part))
                new_po = get_full_path(OriginNamePo(os.path.join(project_path, '.origin'), f.part, f.locale))
                if translations_md5(new_po, is_pos) != translations_md5(old_po, is_pos):
                    self.logger.info("File {}-{} is changed".format(project, get_filename(f)))
                    changed.append(new_po)
                    self.msgmerge(new_po, old_po)
                    shutil.copy(new_po, old_po)
                    if is_pos:
                        out = self.manage('po_from_lp -l {} -c'.format(f.locale))
                        m = re.search("(?<=is converted to )(.*)$", out.decode('utf-8'))
                        if m:
                            self.git('add {}'.format(m.groups()[0]))
                    else:
                        self.git('add {}'.format(old_po))
        msg = "Bug 1194 - {} update translations".format(datetime.date.today())
        if changed and conf['commit']:
            self.logger.info("Changed files: {}".format([item for item in changed]))
            self.git('commit -m', msg)
            self.git('push')


if __name__ == "__main__":
    cmd = Commit()
    cmd.execute()
