import json
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


def save_txt(file_path, data):
    with open(file_path, 'w') as f:
        f.write(data)

    return True

def load_txt(file_path):
    with open(file_path) as f:
        data = f.read()

    return data

def load_json(file_path):
    with open(file_path) as f:
        data = json.load(f)

    return data

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f)

    return True
