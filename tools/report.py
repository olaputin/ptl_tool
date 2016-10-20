from collections import namedtuple
import os
import re
import codecs
from tools import conf
import csv

parts = ['django', 'djangojs', 'pos']
ReleaseCount = namedtuple('ReleaseCount', parts)
CountType = namedtuple('Count', ['lines', 'words'])
MsgIds = namedtuple('MsgIds', parts)
ReleaseInfo = namedtuple('ReleaseInfo', ['name', 'count', 'msgids'])


def changed_lines(prev, cur):
        return ReleaseCount(cur.django-prev.django, cur.djangojs-prev.djangojs, cur.pos-cur.pos)


def count_pos():
    result = dict()
    strings_filename = os.path.join(conf['backend']['path'], 'core/languagepackage/strings.c')
    with codecs.open(strings_filename, encoding='utf8') as f_english:
        for line in f_english.readlines():
            if '=' in line:
                match_obj = re.search(r'"(.*?)"\s*=\s*"(.*?)";', line, flags=re.DOTALL)
                if match_obj:
                    identifier = match_obj.group(1)
                    phrase = match_obj.group(2)
                    result[identifier] = phrase
    result = set(result.values())
    words = ' '.join(result).split()
    return CountType(len(result), len(words)), result


def count_translated_pos(locale):
    csv_filename = os.path.join(conf['backend']['path'], 'lang_packages/lp_official_{}.csv'.format(locale.upper()))
    translated_result = {}
    with open(csv_filename, 'r') as f_english:
        reader = csv.reader(f_english, delimiter=',')
        for row in reader:
            translated_result[row[0]] = row[1]

    english_result = {}
    strings_filename = os.path.join(conf['backend']['path'], 'core/languagepackage/strings.c')
    with codecs.open(strings_filename, encoding='utf8') as f_english:
        for line in f_english.readlines():
            if '=' in line:
                match_obj = re.search(r'"(.*?)"\s*=\s*"(.*?)";', line, flags=re.DOTALL)
                if match_obj:
                    identifier = match_obj.group(1)
                    phrase = match_obj.group(2)
                    english_result[identifier] = phrase

    result = set(translated_result.keys())
    words = ' '.join([english_result.get(key, '') for key in translated_result.keys()]).split()
    return CountType(len(result), len(words))
