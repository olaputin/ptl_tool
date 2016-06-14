import shutil
from os import chdir, path, listdir, makedirs

import tool
from command import Command
from save import Save
from tool import conf, get_locale_path, remove_pyc_files


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
        if not path.exists(project_path):
            makedirs(project_path)
        locale_list = tool.get_loc_list()
        for l in locale_list:
            if conf['languages'] and l not in conf['languages']:
                continue
            self.copy_locale_files(project_path, l)

    def copy_locale_files(self, project_path, locale):
        self.logger.info("locale -{}- in progress".format(locale))
        files_dir = get_locale_path(locale)
        for f in listdir(files_dir):
            if f.endswith('.po'):
                shutil.copy(path.abspath(path.join(files_dir, f)),
                            path.join(project_path, '{}-{}.po'.format(path.splitext(f)[0], locale)))
                self.logger.info(path.abspath(path.join(files_dir, f)))


if __name__ == "__main__":
    cmd = Checkout()
    cmd.execute()

