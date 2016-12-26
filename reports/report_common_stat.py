import os
from polib import pofile
from tools import conf, get_locale_path, remove_pyc_files
from tools.report import ReleaseCount, ReleaseInfo, CountType, parts, MsgIds, count_pos
from command import Command
from collections import OrderedDict
import csv


class CreateReport(Command):

    def __init__(self):
        super().__init__()

    @staticmethod
    def count_file(pf, translated=False):
        msgids = [entry.msgid for entry in (pf if not translated else pf.translated_entries())]
        words = ' '.join(msgids).split()
        return CountType(len(msgids), len(words))

    def execute(self):
        os.chdir(conf['backend']['path'])
        results = OrderedDict()
        locale_path = get_locale_path('de')
        releases = sorted(conf['release']['enable'])
        for i, r in enumerate(releases):
            remove_pyc_files()
            self.update_backend(conf['release']['available'][r])
            msgids, counts = [], []
            for part in parts:
                if part == "pos":
                    nums, ids = count_pos()
                    msgids.append(ids)
                    counts.append(nums)
                else:
                    po_part = pofile(os.path.join(locale_path, part+'.po'))
                    msgids.append(set([entry.msgid for entry in po_part]))
                    counts.append(self.count_file(po_part))
            msgids = MsgIds(*msgids)
            results[r] = ReleaseInfo(r, ReleaseCount(*counts), msgids)

        csv_stat_results = []
        for r in results.values():
            print("*"*3, "release = {}".format(r.name), "*"*3)
            common_words, common_lines, common_django_words, common_django_lines = 0, 0, 0, 0
            for field in r.count._fields:
                nums = r.count.__getattribute__(field)
                common_words += nums.words
                common_lines += nums.lines
                if field.startswith('django'):
                    common_django_lines += nums.lines
                    common_django_words += nums.words
                print("{} = {} / {}".format(field, *nums))

            csv_stat_results.append({'release': r.name,
                       'p_lines': r.count.pos.lines,
                       'p_words': r.count.pos.words,
                       't_lines': common_lines,
                       't_words': common_words,
                       'd_lines': common_django_lines,
                       'd_words': common_django_words
                       })

            print("common_django = {} / {}".format(common_django_lines, common_django_words))
            print("common = {} / {}\n".format(common_lines, common_words))

        changes = OrderedDict()
        for i, r in enumerate(releases[2:], 2):
            prev_info = results[releases[i-1]]
            cur_info = results[r]
            res_parts = []
            for part in parts:
                line_diff = cur_info.msgids.__getattribute__(part) - prev_info.msgids.__getattribute__(part)
                res_parts.append(line_diff)
            changes[r] = ReleaseCount(*[CountType(len(count), len(' '.join(count).split())) for count in res_parts])

        prev_info = results[releases[-1]]
        cur_info = results[releases[0]]
        res_parts = []
        for part in parts:
            line_diff = cur_info.msgids.__getattribute__(part) - prev_info.msgids.__getattribute__(part)
            res_parts.append(line_diff)
        changes[cur_info.name] = ReleaseCount(*[CountType(len(count), len(' '.join(count).split())) for count in res_parts])

        csv_changes_results = []
        print("-"*5, "Changes Lines", "-"*5, '\n')
        for name, r in changes.items():
            common_django_words, common_django_lines = 0, 0
            print("*"*3, "release = {}".format(name), "*"*3)
            for field in r._fields:
                nums = r.__getattribute__(field)
                if field.startswith('django'):
                    common_django_lines += nums.lines
                    common_django_words += nums.words
                print("{} = {:+d} / {:+d}".format(field, *nums))
            csv_changes_results.append({
                'release': name,
                'n_lines': r.django.lines + r.djangojs.lines + r.pos.lines,
                'n_words': r.django.words + r.djangojs.words + r.pos.words
            })
            print("common_django = {:+d} / {:+d}\n".format(common_django_lines, common_django_words))

        os.chdir(os.path.dirname(__file__))

        with open("release_stats.csv", 'w') as f:
            fields = ['release', 'd_lines', 'd_words', 'p_lines', 'p_words', 't_lines', 't_words']
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            writer.writerows(csv_stat_results)

        with open('release_changes_stats.csv', 'w') as f:
            fields = ['release', 'n_lines', 'n_words']
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            writer.writerows(csv_changes_results)


if __name__ == "__main__":
    cmd = CreateReport()
    cmd.execute()
