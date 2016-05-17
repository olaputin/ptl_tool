import polib
import subprocess

from collections import defaultdict
from os import listdir, path, makedirs
from tool import conf, pootle

tm_path = path.join(conf['translations']['path'], '.translation_memory')


def collect_tm():
    main_file = defaultdict(lambda: defaultdict(list))
    for project in conf['release']:
        project_dir = path.join(conf['translations']['path'], project)
        print 'project = {}'.format(project)

        for po_file in listdir(project_dir):
            if po_file.endswith('.po'):
                print 'file = {}'.format(po_file)
                filename = path.splitext(po_file)[0]
                print filename
                part, locale = filename.split('-')
                collect_dict = main_file['{}-{}'.format(part, locale)]
                if conf['languages'] and locale not in conf['languages']:
                    continue
                print 'part = {}-{}'.format(part, locale)
                pofile = polib.pofile(path.join(project_dir, po_file))
                for entry in pofile:
                    if entry.msgstr and entry.msgstr not in collect_dict[entry.msgid]:
                        collect_dict[entry.msgid].append(entry.msgstr)
    return main_file


def save_tm():
    main_file = collect_tm()
    for name, part in main_file.iteritems():
        trans_po = polib.POFile()
        print '--------------- {} -----------------'.format(name)
        for msgid, listmstr in part.iteritems():
            if not len(listmstr) > 1:
                trans_po.append(polib.POEntry(msgid=msgid,
                                              msgstr=listmstr[0]))
            else:
                print "!!!Conflict {}".format(listmstr)
        if not path.exists(tm_path):
            makedirs(tm_path)
        trans_po.save(path.join(tm_path, ''.join([name, '.po'])))
    return main_file


def sync_translation_memory(t_memory):
    print "sync_translations"
    for project in conf['release']:
        project_dir = path.join(conf['translations']['path'], project)

        for po_file in listdir(project_dir):
            if po_file.endswith('.po'):
                filename = path.splitext(po_file)[0]
                part, locale = filename.split('-')
                if conf['languages'] and locale not in conf['languages']:
                    continue

                src_trans = polib.pofile(path.join(project_dir, po_file))

                print 'src_trans = {}'.format(path.join(project_dir, po_file))
                print 't_memory = {}'.format(path.join(tm_path, '-'.join([part, locale])+'.po'))
                src_untranslated = src_trans.untranslated_entries()
                part_memory = t_memory['-'.join([part, locale])]
                for src_entry in src_untranslated:
                    entry = part_memory[src_entry.msgid]
                    if entry:
                        if len(entry) == 1:
                            src_entry.msgstr = entry[0]
                        else:
                            print "Conflict"
                src_trans.save()

                print "po_file = {} locale={}".format(po_file, locale)


def save():
    # update from database
    pootle('sync_stores')
    t_memory = save_tm()
    sync_translation_memory(t_memory)
    pootle('update_stores')
    # subprocess.call([conf['pootle'], 'update_stores'])
    # subprocess.call([conf['pootle'], 'refresh_stats'])
    # print 'finish time = {}'.format(finish)

if __name__ == '__main__':
    save()
