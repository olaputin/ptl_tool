import datetime
import os
import re
import shutil

from rq.decorators import job

from command import Command, CompilemsgException, LngPkgTestException
from tools import conf, get_locale_path, translations_md5, remove_pyc_files, redis_connection
from tools.pofiles import SplitNamePo, OriginNamePo, BackendNamePo, \
    get_full_path, get_filename, get_po_files


class Commit(Command):

    def __init__(self):
        super(Commit, self).__init__()

    def execute(self):
        result = {}
        self.logger.info("Start commit processing")
        os.chdir(conf['backend']['path'])
        for project in conf['release']['enable']:
            release = conf['release']['available'][project]
            remove_pyc_files(conf['backend']['path'])
            self.git('clean -f')
            result = self.process_project(project, release)
        self.set_last_execute()
        self.logger.info("Finish commit processing")
        return result

    def process_project(self, project, release):
        result = {
            'status': True,
            'lng_test': {'status': True,
                         'out': ''},
            'compilemessages': {'status': True,
                                'out': ''}
        }

        if not self.update_backend(release):
            return

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
                        m = re.search("(?<=is converted to )(.*)$", out)
                        if m:
                            self.git('add {}'.format(m.groups()[0]))
                    else:
                        self.git('add {}'.format(old_po))
        self.git('clean -f')
        try:
            self.compilemessages()
            self.test_lng_pkgs()
        except CompilemsgException as ex:
            self.logger.error(ex)
            result['compilemessages'] = {'status': False, 'out': ex}
        except LngPkgTestException as ex:
            self.logger.error(ex)
            result['lng_test'] = {'status': False, 'out': ex}

        result['status'] = all([result[part]['status'] for part in ['compilemessages', 'lng_test']])
        msg = "Bug 1194 - {} update translations".format(datetime.date.today())
        if not result['status'] and changed:
            self.logger.info("Changed files: {}".format([item for item in changed]))
            self.git('commit -m', msg)
            self.git('push')

        return result

    def test_lng_pkgs(self):
        output = self.manage('test --noinput tests.test_language_package')
        if not re.search(r"OK", output):
            raise LngPkgTestException(output)


@job('commit', connection=redis_connection())
def run():
    cmd = Commit()
    return cmd.execute()

if __name__ == "__main__":
    run()
