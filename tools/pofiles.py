import os
import glob
from collections import namedtuple


SplitNamePo = namedtuple('SplitName', ['path', 'part', 'split', 'locale'])
OriginNamePo = namedtuple('OriginName', ['path', 'part', 'locale'])
BackendNamePo = namedtuple('ProjectNamePo', ['path', 'part'])


def get_parts(full_path, file_type):
    file_path, filename = os.path.split(full_path)
    filename, _ = os.path.splitext(filename)
    return file_type(file_path, *filename.split('-'))


def get_po_files(full_path, type_files):
    for item in glob.glob(os.path.join(full_path, "*.po")):
        yield get_parts(item, type_files)


def get_filename(file_obj):
    return "-".join(file_obj[1:])+".po"


def get_full_path(file_obj):
    return os.path.join(file_obj[0], get_filename(file_obj))
