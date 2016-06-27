import logging
import subprocess
import time
import re
from datetime import datetime
from logging import config

from tools import conf, get_loc_list, redis_connection


class CompilemsgException(Exception):
    pass


class LngPkgTestException(Exception):
    pass


class Command(object):
    def __init__(self):
        config.dictConfig(conf['logging'])
        self.name = self.__class__.__name__.lower()
        self.logger = logging.getLogger(self.name)

    def execute(self):
        raise NotImplemented()

    def update_backend(self, release):
        self.git('stash')
        self.git('fetch')
        self.git('checkout {}'.format(release))
        self.git('pull origin {}'.format(release))
        langs = conf['languages'] if conf['languages'] else get_loc_list()
        makemessages = "makemessages -l {} {} --no-wrap --no-default-ignore --symlinks"
        for l in langs:
            if conf['makemessages']['backend']:
                self.manage(makemessages.format(l, '-e html,txt,py,htm,ejs'))   # for django files
                self.manage(makemessages.format(l, '-d djangojs'))              # for js files.
        try:
            self.compilemessages()
        except CompilemsgException as ex:
            self.logger.error(ex)
            return False

        # TODO: make in one loop
        for l in langs:
            if conf['makemessages']['pos']:
                try:
                    self.manage('po_from_lp -f -l {}'.format(l))                # for pos files
                except subprocess.CalledProcessError as ex:
                    self.logger.error("Can't generate pos file! Exception: {}".format(ex))
        return True

    def compilemessages(self):
        if conf['compilemessages']:
            for cmd in ['compilemessages', 'compilejsi18n']:
                output = self.manage(cmd)
                if re.search(r"CommandError:", output):
                    raise CompilemsgException(output)

    def git(self, command, msg=None):
        cmd = command.split(' ')
        if conf['git']['enable'] and conf['git'].get(cmd[0], True):
            cmd = ['git'] + command.split(' ') + ([msg] if msg else [])
            self.call(cmd)

    def pootle(self, command):
        if conf['pootle']['enable']:
            cmd = [conf['pootle']['bin']] + command.split(' ')
            self.call(cmd)

    def msgmerge(self, new, old):
        cmd = [conf['msgmerge'], '-U', new, old]
        self.call(cmd)

    def manage(self, command, logger=None):
        cmd = [conf['backend']['bin'], 'manage.py'] + command.split(' ')
        _, output = self.call(cmd)
        return output

    def call(self, cmd):
        self.logger.info('Subprocess: ' + ' '.join(cmd))
        try:
            command_line_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            process_output, _ = command_line_process.communicate()
            self.logger.info(process_output.decode('utf-8'))
        except (OSError, subprocess.CalledProcessError) as exception:
            self.logger.info('Exception occured: ' + str(exception))
            self.logger.info('Subprocess failed')
            return False, ''
        else:
            # no exception was raised
            self.logger.info('Subprocess finished')
        return True, process_output.decode('utf-8')

    @property
    def last_execute(self):
        return redis_connection().get('ptl:{}:last_exec'.format(self.name))

    def set_last_execute(self):
        redis_connection().set('ptl:{}:last_exec'.format(self.name), time.mktime(datetime.utcnow().timetuple()))

