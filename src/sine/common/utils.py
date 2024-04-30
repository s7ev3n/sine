import os
import re
from dataclasses import asdict
from enum import IntEnum


def enum_dict_factory(inputs):
    inputs = [(i[0], i[-1].value) if isinstance(i[-1], IntEnum) else i
              for i in inputs]
    return dict(inputs)


def dataclass2dict(data):
    return asdict(data, dict_factory=enum_dict_factory)

def make_dir_if_not_exist(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def is_valid_url(url):
    pattern = re.compile(r'^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    if pattern.match(url):
        return True
    else:
        return False
