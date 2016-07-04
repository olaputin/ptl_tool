import json
from collections import defaultdict
from os import path, makedirs

import polib
import shutil

from command import Command
from tools import conf
from tools.pofiles import SplitNamePo, OriginNamePo, get_po_files, get_full_path, get_filename

tm_path = path.join(conf['translations']['path'], '.translation_memory')


class Save(Command):

    def __init__(self):
        super(Save, self).__init__()

    def execute(self):
        self.logger.info('Start save processing')
        for project in conf['release']['enable']:
            self.pootle('sync_stores --force --overwrite --project={}'.format(project))
        # work with translation memory
        t_memory = self.save_tm()
        self.sync_translation_memory(t_memory)
        # union of splitted parts
        self.collect_splitted()
        for project in conf['release']['enable']:
            self.pootle('update_stores --project={}'.format(project))
        self.pootle('refresh_stats')
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
            project_index = conf['release']['available'][project].get('index', conf['release']['default_index'])
            for f in get_po_files(project_dir, SplitNamePo):
                self.logger.info('project={} file = {}'.format(project, get_full_path(f)))
                collect_dict = main_file['-'.join([f.part, f.locale])]
                if conf['languages'] and f.locale not in conf['languages']:
                    continue
                pofile = polib.pofile(get_full_path(f))
                for entry in pofile:
                    if entry.msgstr and not entry.obsolete and 'fuzzy' not in entry.flags:
                        collect_dict[entry.msgid].append((entry.msgstr, project_index))
        return main_file

    def save_tm(self):
        # collect translation memory during all enabled releases
        main_file = self.collect_tm()

        # remove old .translation memory and create new
        if path.exists(tm_path):
            shutil.rmtree(tm_path)
        makedirs(tm_path)

        # save to files collected items of translation memory
        for name, part in main_file.items():
            trans_po = polib.POFile()
            for msgid, listmstr in part.items():
                if len(listmstr) > 0:
                    # get entry with max index
                    listmstr.sort(key=lambda x: x[1], reverse=True)
                    msgstr, max_index = listmstr[0]
                    trans_po.append(polib.POEntry(msgid=msgid,
                                                  msgstr=msgstr))
                    if len(listmstr) > 1:
                        self.logger.info(u"Conflict {}: {}".format(msgid, listmstr))
                        self.logger.info(u"Choosen index: {}".format(max_index))
            trans_po.save(path.join(tm_path, ''.join([name, '.po'])))
        return main_file

    def sync_translation_memory(self, t_memory):
        self.logger.info("sync_translations")
        for project in conf['release']['enable']:
            project_dir = path.join(conf['translations']['path'], project)

            for f in get_po_files(project_dir, SplitNamePo):
                if conf['languages'] and f.locale not in conf['languages']:
                    continue

                src_trans = polib.pofile(get_full_path(f))

                self.logger.info('src_trans = {}'.format(get_full_path(f)))
                self.logger.info('t_memory = {}'.format(get_full_path(OriginNamePo(tm_path, f.part, f.locale))))
                # src_untranslated = [e for e in src_trans if not e.translated() and not e.obsolete]
                part_memory = t_memory['-'.join([f.part, f.locale])]
                for src_entry in src_trans:  # for all src
                    entry = part_memory[src_entry.msgid]
                    if entry:
                        new_msgstr, _ = entry[0]
                        self.logger.info("{} changed {}: {} - {}".format('fuzzy' if 'fuzzy' in src_entry.flags else '',
                                                                         src_entry.msgid, src_entry.msgstr, new_msgstr))
                        src_entry.msgstr = new_msgstr
                        if 'fuzzy' in src_entry.flags:
                            src_entry.flags.remove('fuzzy')
                src_trans.save()

                self.logger.info("po_file = {} locale={}".format(get_filename(f), f.locale))

    def sync_splitted(self):
        self.logger.info("sync splitted files")
        for project in conf['release']['enable']:
            splitted_dir = path.join(conf['translations']['path'], project)

            for f in get_po_files(splitted_dir, SplitNamePo):
                if conf['languages'] and f.locale not in conf['languages']:
                    continue
                print(f)


def run():
    cmd = Save()
    cmd.execute()
    return json.dumps({'status': 'finished'})

if __name__ == '__main__':
    run()
