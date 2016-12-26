import codecs
import os
import re
from argparse import ArgumentParser
from collections import OrderedDict, defaultdict

from tools import conf


def get_dict_from_strings(strings_filename, ignore_not_translnatable=True, ordered=False):
    """

    :param strings_filename: A name of .strings file to extract data from.
    :param ignore_not_translnatable: Ignore "Do not translate" comments, add lines
     with this comment to dictionary too.
    :return: Dict {<msgId>: <msgStr>, ..} for all phrases from given .strings file,
    where msgId is something line 'BtnErrMsg' - an identifier of localizable phrase,
    and msgstr is a phrase itself in current language.
    """
    result = OrderedDict() if ordered else dict()
    with codecs.open(strings_filename, encoding='utf8') as f_english:
        for line in f_english.readlines():
            if '=' in line:
                if ignore_not_translnatable:
                    no_spaces_lowercase_line = ''.join(line.lower().split())
                    if ('donottranslate' in no_spaces_lowercase_line or
                            'donttranslate' in no_spaces_lowercase_line or
                            "don'ttranslate" in no_spaces_lowercase_line):
                        continue
                match_obj = re.search(r'"(.*?)"\s*=\s*"(.*?)";', line, flags=re.DOTALL)
                if match_obj:
                    identifier = match_obj.group(1)
                    phrase = match_obj.group(2)
                    result[identifier] = phrase
    return result


def get_localizable_strings_path(repo_path):
    lang_pack_path_to_test = os.path.join(repo_path, 'POS/POS/en.lproj/Localizable.strings')
    if not os.path.exists(lang_pack_path_to_test):
        raise ValueError('Localizable.strings is not found in any of given paths')
    return lang_pack_path_to_test


def get_occurrence_msg_id(repo_root, check_list_msg_id):
    occurrences = defaultdict(list)
    for root, dirs, files in os.walk(repo_root):
        if '/.git' in root:
            continue
        for name in files:
            if not (name.endswith('.xib') or name.endswith('.m') or name.endswith('.h')
                    or name.endswith('.storyboard')):
                continue

            file_path = os.path.join(root, name)
            with codecs.open(os.path.join(root, name), "r", encoding='utf-8') as sourcefile:
                filecontent = sourcefile.read()
                for mid in check_list_msg_id:
                    if mid in filecontent:
                        occurrences[mid].append(file_path[len(repo_root):])
    return occurrences


if __name__ == '__main__':
    repo_path = conf['pos']['path']

    backend_path = conf['backend']['path']
    result_full_path = os.path.join(os.path.join(backend_path, 'lang_packages'), 'pos_occurrences.txt')
    lang_pack_path_to_test = get_localizable_strings_path(repo_path)

    english_dict_keys = set(get_dict_from_strings(lang_pack_path_to_test).keys())
    occurrences = get_occurrence_msg_id(repo_path, english_dict_keys)

    with codecs.open(result_full_path, 'w') as result:
        result.writelines(["{}:{}\n".format(msg_id, ','.join(set(occurrences[msg_id]))) for msg_id in occurrences])









