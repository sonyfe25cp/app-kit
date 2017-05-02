from tornado import template

import argparse
import os
import logging

FORMAT = '%(asctime)-15s %(name)s:%(lineno)d %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

parser = argparse.ArgumentParser(description="Generate alading xml")

parser.add_argument('--input', type=str, default='', help='definition file')
parser.add_argument('--out', type=str, default="", help='output dir')
parser.add_argument('--test', type=bool, default=True, help='update test code')

ARGS = parser.parse_args()

DIR = os.path.abspath(os.path.dirname(__file__))
TYPES = {
    'i64': (8, 'long'),
    'i32': (4, 'int'),
    'i16': (2, 'short'),
    'byte': (1, 'byte'),
}


class Field(object):
    def __init__(self, off, name, t):
        # 4 => the first 4 bytes are for length
        self.off = off + 4
        self.name = name
        self.Name = name[0].upper() + name[1:]

        len, java = TYPES[t]


        self.java = java
        if java == 'byte':
            self.Java = ''
        else:
            self.Java = java[0].upper() + java[1:]
        self.len = len


def parse_file(f):
    fields = []

    off = 0

    for line in open(f).readlines():
        if '{' in line or '}' in line or not line.strip():
            continue

        t, name = line.strip().split()

        if t not in TYPES:
            raise Exception('%s is not a known type', t)

        len, java = TYPES[t]

        fields.append(Field(off, name, t))

        off += len

    # all fields,
    return fields, off


def gen_java_file():
    fields, off = parse_file('/home/feng/workspace/engine/py-scripts/s4j/mmap.def')

    loader = template.Loader(DIR, autoescape=None)
    # folder = dbapi.namespace.replace('.', '/')

    java = loader.load('mmap.tpl').generate(
        cls='JobProperty2',
        ns='test',
        sizeof=off,
        fields=fields
    )
    print java

    pass


if __name__ == '__main__':
    gen_java_file()