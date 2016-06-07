from collections import defaultdict
from os import listdir, path, makedirs

import polib

from command import Command
from tool import conf

tm_path = path.join(conf['translations']['path'], '.translation_memory')


class Save(Command):

    def __init__(self):
        super(Save, self).__init__()

    # @job('save', connection=redis_connection())
    def execute(self):
        self.logger.info('Start save processing')
        for project in conf['release']['enable']:
            self.pootle('sync_stores --force --overwrite --project={}'.format(project))
        t_memory = self.save_tm()
        self.sync_translation_memory(t_memory)
        self.pootle('update_stores')
        self.pootle('refresh_stats')
        self.set_last_execute()
        self.logger.info('Finish save processing')
        return True

    def collect_tm(self):
        main_file = defaultdict(lambda: defaultdict(list))
        for project in conf['release']['enable']:
            project_dir = path.join(conf['translations']['path'], project)

            for po_file in listdir(project_dir):
                if po_file.endswith('.po'):
                    self.logger.info('project={} file = {}'.format(project, po_file))
                    filename = path.splitext(po_file)[0]
                    part, locale = filename.split('-')
                    collect_dict = main_file['{}-{}'.format(part, locale)]
                    if conf['languages'] and locale not in conf['languages']:
                        continue
                    pofile = polib.pofile(path.join(project_dir, po_file))
                    for entry in pofile:
                        if entry.msgstr and entry.msgstr not in collect_dict[entry.msgid] and 'fuzzy' not in entry.flags:
                            collect_dict[entry.msgid].append(entry.msgstr)
        return main_file

    def save_tm(self):
        main_file = self.collect_tm()
        for name, part in main_file.iteritems():
            trans_po = polib.POFile()
            for msgid, listmstr in part.iteritems():
                if len(listmstr) == 1:  # only one value for this id
                    trans_po.append(polib.POEntry(msgid=msgid,
                                                  msgstr=listmstr[0]))
                elif len(listmstr) > 1:
                    self.logger.info(u"Conflict {}: {}".format(msgid, listmstr))
            if not path.exists(tm_path):
                makedirs(tm_path)
            trans_po.save(path.join(tm_path, ''.join([name, '.po'])))
        return main_file

    def sync_translation_memory(self, t_memory):
        self.logger.info("sync_translations")
        for project in conf['release']['enable']:
            project_dir = path.join(conf['translations']['path'], project)

            for po_file in listdir(project_dir):
                if po_file.endswith('.po'):
                    filename = path.splitext(po_file)[0]
                    part, locale = filename.split('-')
                    if conf['languages'] and locale not in conf['languages']:
                        continue

                    src_trans = polib.pofile(path.join(project_dir, po_file))

                    self.logger.info('src_trans = {}'.format(path.join(project_dir, po_file)))
                    self.logger.info('t_memory = {}'.format(path.join(tm_path, '-'.join([part, locale])+'.po')))
                    src_untranslated = src_trans.untranslated_entries()
                    part_memory = t_memory['-'.join([part, locale])]
                    for src_entry in src_untranslated:
                        entry = part_memory[src_entry.msgid]
                        if entry:
                            if len(entry) == 1:
                                src_entry.msgstr = entry[0]
                            else:
                                self.logger.info(u"Conflict {}: {}".format(src_entry.msgid, entry))
                    src_trans.save()

                    self.logger.info("po_file = {} locale={}".format(po_file, locale))


if __name__ == '__main__':
    cmd = Save()
    cmd.execute()
