import csv
import os
from datetime import datetime, timedelta

from dateutil import parser
from polib import pofile

from command import Command
from reports.report_common_stat import parts, ReleaseCount, CreateReport, CountType, ReleaseInfo, MsgIds
from tools import conf, get_locale_path, remove_pyc_files
from tools.report import count_pos

day_format = "%Y-%m-%d"
locale = 'de'


class WeekRepReport(Command):
    def __init__(self):
        super().__init__()

    def execute(self):
        os.chdir(conf['backend']['path'])
        locale_path = get_locale_path(locale)
        results = {}

        self.update_backend(conf['release']['available']['master'])
        _, logs = self.git("log", "--pretty=tformat:%aI,%H")
        logs = logs.split('\n')[:-1]
        commits = {}
        for commit in logs:
            d, hash = commit.split(',')
            commits[parser.parse(d).strftime(day_format)] = hash

        # need_day = datetime(2016, 7,  5, 0, 0, 0)
        need_day = datetime(2016, 1,  7, 0, 0, 0)
        period = timedelta(days=7)

        need_hash = {}
        now = datetime.now()
        while need_day < now:
            need_day_format = need_day.strftime(day_format)
            need_hash[need_day_format] = commits[need_day_format]
            need_day += period

        for day in sorted(need_hash.keys()):
            print("{} = {}".format(day, need_hash[day]))
            self.git('stash')
            remove_pyc_files()
            self.git("checkout", need_hash[day])
            makemessages = "makemessages -l {} {} --no-wrap --no-default-ignore --symlinks"
            if conf['makemessages']['backend']:
                self.manage(makemessages.format('de', '-e html,txt,py,htm,ejs'))   # for django files
                self.manage(makemessages.format('de', '-d djangojs'))              # for js files.
            # self.manage('po_from_lp -f -l de')

            msgids, counts = [], []
            for part in parts:
                if part != "pos":
                    po_part = pofile(os.path.join(locale_path, part+'.po'))
                    msgids.append(set([entry.msgid for entry in po_part]))
                    counts.append(CreateReport.count_file(po_part))
                else:
                    num, ids = count_pos()
                    counts.append(num)
                    msgids.append(ids)
                # print("part={} count={}".format(part, counts[-1]))

            results[day] = ReleaseInfo(day, ReleaseCount(*counts), MsgIds(*msgids))

        csv_results = []
        start_week = 2
        prev_week = None
        diff = None
        for i, day in enumerate(sorted(results.keys()), start_week):
            result = results[day]
            if prev_week:
                week_diff = []
                print("start_week")
                for part in parts:
                    week_diff.append(result.msgids.__getattribute__(part) - prev_week.msgids.__getattribute__(part))
                diff = ReleaseCount(*[CountType(len(count), len(' '.join(count).split())) for count in week_diff])
            print("Day = {}".format(day))
            info = {'day': day,
                    'num_week': i,
                    'p_lines': result.count.pos.lines,
                    'p_words': result.count.pos.words,
                    'd_lines': result.count.django.lines + result.count.djangojs.lines,
                    'd_words': result.count.django.words + result.count.djangojs.words
                    }
            info['t_lines'] = info['p_lines'] + info['d_lines']
            info['t_words'] = info['p_words'] + info['d_words']
            if diff:
                info['diff_lines'] = sum([diff.__getattribute__(part).lines for part in parts])
                info['diff_words'] = sum([diff.__getattribute__(part).words for part in parts])
            csv_results.append(info)

            for part in parts:
                print("{} = {} / {} ".format(part, *results[day].count.__getattribute__(part)))
            print("\n")
            prev_week = results[day]

        os.chdir(os.path.dirname(__file__))
        with open('result_master.csv', 'w') as f:
            fieldsname = ['num_week', 'day', 'd_lines', 'd_words', 'p_lines', 'p_words', 't_lines', 't_words', 'diff_lines', 'diff_words']
            writer = csv.DictWriter(f, fieldnames=fieldsname)
            writer.writeheader()
            writer.writerows(csv_results)


if __name__ == "__main__":
    cmd = WeekRepReport()
    cmd.execute()
