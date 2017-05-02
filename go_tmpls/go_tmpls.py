# encoding: utf8

__author__ = 'feng'
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import re
import logging
import argparse
from tornado import template
import os

FORMAT = '%(asctime)-15s %(name)s:%(lineno)d %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

parser = argparse.ArgumentParser(description="Generate alading xml")

parser.add_argument('-dir', type=str, default='', help='Where to search for template files')
parser.add_argument('-regex', type=str, default="", help='Template regex')
parser.add_argument('-ignore', type=str, default=".*\.go", help='Ignore tmplate')
parser.add_argument('-o', type=str, default="tmpls.go", help='Generated file name')
parser.add_argument('-pkg', type=str, default="main", help='Generated package name')
parser.add_argument('-mode', type=str, default="debug", help='Debug or release mode')

ARGS = parser.parse_args()

DIR = os.path.abspath(os.path.dirname(__file__))


def generate_file():
    dir = os.path.abspath(ARGS.dir)
    tmpls = []

    regex = re.compile(ARGS.regex) if ARGS.regex else None
    ignore = re.compile(ARGS.ignore) if ARGS.ignore else None

    for root, dirs, files in os.walk(dir):
        for f in files:

            if regex and not regex.search(f):
                logging.info("not match %s", f)
                continue
            if ignore and ignore.search(f):
                logging.info("ignore file %s", f)
                continue

            path = '%s/%s' % (root, f)
            name = path[path.index(dir) + len(dir):].strip('/')  # 干掉前面的路径

            name = name[:name.index('.')]  # 干掉扩展名

            method = name[0].upper() + name[1:]  # golang的首字母大写
            method = re.sub(r'[/|\\].', lambda x: x.group(0)[1].upper(), method)
            content = open(path).read()
            content = re.sub('\\s+', ' ', content)

            tmpls.append((path, name, method, content))

    t = ",\n".join(['{"%s", "%s", "%s"}' % (path, name, m) for path, name, m, content in tmpls])
å
    arrs = "[][]string{%s}" % t

    loader = template.Loader(DIR, autoescape=None)
    code = loader.load("tmpls.go.tpl").generate(pkg=ARGS.pkg, tmpls=tmpls, arrs=arrs, mode=ARGS.mode)
    dir = os.path.dirname(ARGS.o)
    if not os.path.isdir(dir) and dir:
        os.makedirs(dir)
    code = code.decode("utf-8")
    open(ARGS.o, 'w').write(code)


if __name__ == '__main__':
    generate_file()
