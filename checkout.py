import glob
import re
import shutil
from os import chdir, path, makedirs

import polib

from command import Command
from tools import conf, get_locale_path, remove_pyc_files, convert_split_confs, get_loc_list
from tools.pofiles import BackendNamePo, OriginNamePo, SplitNamePo, \
    get_po_files, get_full_path


class Checkout(Command):
    def __init__(self):
        super(Checkout, self).__init__()

    # @job('checkout', connection=tool.redis_connection())
    def execute(self):
        self.logger.info('Start checkout processing')
        chdir(conf['backend']['path'])
        for project in conf['release']['enable']:
            release = conf['release']['available'][project]
            remove_pyc_files(conf['backend']['path'])
            self.git('clean -f')
            self.update_backend(release)
            self.process_project(project)
            self.pootle('update_stores --force --overwrite --project={}'.format(project))
        self.set_last_execute()
        self.logger.info('Finish checkout processing')

    def process_project(self, project):
        project_path = path.join(conf['translations']['path'], project)

        if path.exists(project_path):
            shutil.rmtree(project_path)

        for dp in [project_path, path.join(project_path, '.origin')]:
            makedirs(dp)

        for l in get_loc_list():
            if conf['languages'] and l not in conf['languages']:
                continue
            self.copy_locale_files(project_path, l, project)

    def _is_splited(self, split_name, entry, result_files):
        places = dict([(p, line) for p, line in entry.occurrences])
        if len(places) == 1:
            for place in places:
                for pattern in conf['split'][split_name]['path']:
                    if re.match(pattern, place):
                        split_file = result_files.setdefault(split_name, polib.POFile())
                        split_file.append(entry)
                        return True
        return False

    def copy_locale_files(self, project_path, locale, release):
        self.logger.info("Copy split files: {} {}".format(locale, release))
        split_settings = convert_split_confs()
        files_dir = get_locale_path(locale)
        for f in get_po_files(files_dir, BackendNamePo):

            result_files = {}
            split_name = split_settings.get('-'.join([f.part, locale, release]))

            shutil.copy(get_full_path(f), get_full_path(
                OriginNamePo(path.join(project_path, '.origin'), f.part, locale)))

            for entry in polib.pofile(get_full_path(f)):
                if split_name:
                    if self._is_splited(split_name, entry, result_files):
                        continue
                base_file = result_files.setdefault('base', polib.POFile())
                base_file.append(entry)
            for name, res_po in result_files.items():
                res_po.save(get_full_path(SplitNamePo(project_path, f.part, name, locale)))

if __name__ == "__main__":
    cmd = Checkout()
    cmd.execute()

