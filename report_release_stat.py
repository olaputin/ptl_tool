import csv
import os
from command import Command
from report_common_stat import parts, CreateReport
from tools import conf, get_locale_path
from tools.report import count_pos, count_translated_pos
from polib import pofile


class ReleaseStatReport(Command):
    def __init__(self):
        super().__init__()

    def execute(self):
        os.chdir(conf['backend']['path'])
        self.update_backend(conf['release']['available']['master'])
        langs = conf['languages']
        results = {}
        for l in langs:
            umsgids, ucounts = [], []
            counts = []
            for part in parts:
                if part != "pos":
                    po_part = pofile(os.path.join(get_locale_path(l), part+'.po'))
                    umsgids.append(set([entry.msgid for entry in po_part]))
                    ucounts.append(CreateReport.count_file(po_part))
                    counts.append(CreateReport.count_file(po_part, True))
                else:
                    num, ids = count_pos()
                    ucounts.append(num)
                    umsgids.append(ids)
                    counts.append(count_translated_pos(l))
            results[l] = (ucounts, counts)

            csv_results = []
            for locale, value in results.items():
                common, translated = value
                csv_results.append({
                    'locale': locale,
                    'b_common_l': common[0].lines + common[1].lines,
                    'b_common_w': common[0].words + common[1].words,
                    'f_common_l': common[2].lines,
                    'f_common_w': common[2].words,
                    'b_translated_l': translated[0].lines + translated[1].lines,
                    'b_translated_w': translated[0].words + translated[1].words,
                    'f_translated_l': translated[2].lines,
                    'f_translated_w': translated[2].words,
                    'b_percent': "{0:.2f}".format((translated[0].words + translated[1].words)*100/(common[0].words + common[1].words)),
                    'f_percent': "{0:.2f}".format(translated[2].words*100/common[2].words)
                })
                print(locale)

            os.chdir(os.path.dirname(__file__))
            with open('report_release.csv', 'w') as f:
                fieldsname = ['locale', 'b_common_l', 'b_common_w', 'f_common_l', 'f_common_w',
                              'b_translated_l', 'b_translated_w', 'f_translated_l', 'f_translated_w',
                              'b_percent', 'f_percent']
                writer = csv.DictWriter(f, fieldnames=fieldsname)
                writer.writeheader()
                writer.writerows(csv_results)

if __name__ == "__main__":
    cmd = ReleaseStatReport()
    cmd.execute()
