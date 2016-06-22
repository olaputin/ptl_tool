from collections import defaultdict
from os import path, makedirs

import polib

from command import Command
from tools import conf
from tools.pofiles import SplitNamePo, OriginNamePo, get_po_files, get_full_path, get_filename
tm_path = path.join(conf['translations']['path'], '.translation_memory')


class Save(Command):

    def __init__(self):
        super(Save, self).__init__()

    # @job('save', connection=redis_connection())
    def execute(self):
        self.logger.info('Start save processing')
        for project in conf['release']['enable']:
            self.pootle('sync_stores --force --overwrite --project={}'.format(project))
        self.collect_splitted()
        t_memory = self.save_tm()
        self.sync_translation_memory(t_memory)
        self.pootle('update_stores')
        self.pootle('refresh_stats')
        self.set_last_execute()
        self.logger.info('Finish save processing')
        return True

    def collect_splitted(self):
        for project in conf['release']['enable']:
            project_dir = path.join(conf['translations']['path'], project)
            origin_dir = path.join(project_dir, '.origin')
            storage = defaultdict(lambda: defaultdict(list))

            for f in get_po_files(project_dir, SplitNamePo):
                part_storage = storage[(f.part, f.locale)]
                for entry in polib.pofile(get_full_path(f)):
                    part_storage[(entry.msgid, entry.msgctxt)] = entry

            for f in get_po_files(origin_dir, OriginNamePo):
                part_storage = storage[(f.part, f.locale)]
                pofile = polib.pofile(get_full_path(f))
                for entry in pofile:
                    splited_entry = part_storage[(entry.msgid, entry.msgctxt)]
                    if splited_entry:
                        entry.msgstr = splited_entry.msgstr
                        entry.flags = splited_entry.flags
                pofile.save()

    def collect_tm(self):
        main_file = defaultdict(lambda: defaultdict(list))
        for project in conf['release']['enable']:
            project_dir = path.join(conf['translations']['path'], project)

            for f in get_po_files(project_dir, SplitNamePo):
                self.logger.info('project={} file = {}'.format(project, get_full_path(f)))
                collect_dict = main_file['-'.join([f.part, f.locale])]
                if conf['languages'] and f.locale not in conf['languages']:
                    continue
                pofile = polib.pofile(get_full_path(f))
                for entry in pofile:
                    if entry.msgstr and entry.msgstr not in collect_dict[entry.msgid] and 'fuzzy' not in entry.flags:
                        collect_dict[entry.msgid].append(entry.msgstr)
        return main_file

    def save_tm(self):
        main_file = self.collect_tm()
        for name, part in main_file.items():
            trans_po = polib.POFile()
            for msgid, listmstr in part.items():
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
            project_dir = path.join(conf['translations']['path'], project, '.origin')

            for f in get_po_files(project_dir, OriginNamePo):
                if conf['languages'] and f.locale not in conf['languages']:
                    continue

                src_trans = polib.pofile(get_full_path(f))

                self.logger.info('src_trans = {}'.format(get_full_path(f)))
                self.logger.info('t_memory = {}'.format(get_full_path(OriginNamePo(tm_path, f.part, f.locale))))
                src_untranslated = src_trans.untranslated_entries()
                part_memory = t_memory['-'.join([f.part, f.locale])]
                for src_entry in src_untranslated:
                    entry = part_memory[src_entry.msgid]
                    if entry:
                        if len(entry) == 1:
                            src_entry.msgstr = entry[0]
                        else:
                            self.logger.info(u"Conflict {}: {}".format(src_entry.msgid, entry))
                src_trans.save()

                self.logger.info("po_file = {} locale={}".format(get_filename(f), f.locale))

if __name__ == '__main__':
    cmd = Save()
    cmd.execute()
