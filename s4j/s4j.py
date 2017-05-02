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

FORMAT = '%(asctime)-15s %(name)s:%(lineno)d %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

parser = argparse.ArgumentParser(description="Generate alading xml")

parser.add_argument('--input', type=str, default='', help='definition file')
parser.add_argument('--out', type=str, default="", help='output dir')
parser.add_argument('--test', type=bool, default=True, help='update test code')

ARGS = parser.parse_args()

DIR = os.path.abspath(os.path.dirname(__file__))

FUNC = 'func'
STRUCT = 'struct'

TYPE_MAPPING = [
    ('list<i32>', 'List<Integer>'),
    ('list<i64>', 'List<Long>'),
    ('list<', 'List<'),
    ('map<', 'Map<'),
    ('i32', 'int'),
    ('i64', 'long'),
    ('float32', 'float'),
    ('float64', 'double'),
    ('bool', 'boolean'),
    ('string', 'String'),
    ('datetime', 'Timestamp')
]


def convert_to_java_type(t):
    for k, v in TYPE_MAPPING:
        t = t.replace(k, v)

    return t


def java_name2_sql_name(n):
    return re.sub('[A-Z]', lambda x: '_' + x.group().lower(), n)


def parse_sqls(sqls, args):
    sql = ' '.join(sqls)
    args = {name: type for type, name in args}

    # sql = sql.replace('\S+', ' ').replace('\n', '')
    # 去掉多余的空格
    sql = re.sub(r'\s+', ' ', sql)
    # print sql, args

    # 处理一些分库，分表的事情
    # => .+? => non greedy
    sql = re.sub('\\$\\{(.+?)\\}', lambda x: '" +  (%s) + "' % x.group(1), sql)


    # 处理参数
    holders = re.findall(':([a-zA-Z0-9\.]+)', sql)
    sql_args, idx = [], 0

    for h in holders:
        arg = h
        if '.' in arg:
            arg = h.split('.')[0]

        if arg not in args:
            raise Exception(":%s is not an argument in %s" % (h, sql))

        # 处理 list<int>
        if 'List' in args[arg]:
            sql = re.sub(':%s' % h, '" + join(%s) + "' % h, sql)
        else:
            idx += 1
            sql_args.append((idx, h))

    ps_sql = re.sub(':[a-zA-Z0-9\.]+', '?', sql)

    # print ps_sql, sql_args
    return ps_sql, sql_args


def run_tests():
    assert 'company_id' == java_name2_sql_name('companyId')

    input_args = [("int", "id"), ("Bean", "arg")]

    sql, args = parse_sqls(['SELECT * FROM table WHERE id = :id AND name = :arg.name'], input_args)

    assert sql == 'SELECT * FROM table WHERE id = ? AND name = ?'
    assert args == [(1, 'id'), (2, 'arg.name')]
    assert len(args) == 2

    input_args = [("List<Integer>", "ids"), ("Bean", "arg")]
    sql, args = parse_sqls(['SELECT * FROM table WHERE id IN (:ids) AND name = :arg.name'], input_args)

    assert sql == 'SELECT * FROM table WHERE id IN (" + join(ids) + ") AND name = ?'
    assert args == [(1, 'arg.name')]

    input_args = [("int", "id"), ("Bean", "arg"), ('int', 'table_idx')]
    sql, args = parse_sqls(['SELECT * FROM table${table_idx} WHERE id = :id AND NAME = :arg.name'], input_args)

    # print sql, args
    assert sql == 'SELECT * FROM table" +  (table_idx) + " WHERE id = ? AND NAME = ?'
    assert args == [(1, 'id'), (2, 'arg.name')]
    print('tests pass')

    # import sys
    #
    # sys.exit(1)


run_tests()


class Row(dict):
    """A dict that allows for object-like property access syntax."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


METHODS = dict(
    int=('getInt', '0'),
    long=('getLong', '0'),
    String=('getString', "null"),
    Timestamp=('getTimestamp', "null"),
    boolean=('getBoolean', "false"),
    double=('getDouble', '0.0'),
    float=('getFloat', '0.0')
)


class Struct(object):
    def __init__(self, line, api):
        # struct Interview {
        if 'extends' not in line:
            self.name = line.strip('{').split()[-1].strip()
            self.extends = None
        else:
            _, self.name, _, self.extends = line.strip('{').split()
            # struct JobsWithGeo extends FetchedJob
        self.fields = []

        self.api = api

    def add_field(self, line):
        type, name = convert_to_java_type(line.strip(',;').strip()).split()
        self.fields.append((type, name))

    def __str__(self):
        return '%s {\n%s\n}\n' % (self.name, '\n'.join('%s %s' % f for f in self.fields))

    @property
    def fields_rs(self):
        results = []

        # print idx, t, name, '==========================='
        for idx, (t, name) in enumerate(self.fields):
            results.append(Row(
                # var='f%d' % (idx + 1),
                var=name,
                field=java_name2_sql_name(name),
                name=name,
                type=t,
                method=METHODS[t][0]
            ))

        return results


class Func(object):
    def __init__(self, line, api):
        _, resp, name, _ = re.split('\s+|\(', line, 3)
        args = convert_to_java_type(re.search('\((.*)\)', line).group(1)).strip()

        self.raw_resp = resp

        # print self.resp, resp, '-----------------'
        self.name = name
        self.args = []

        self.api = api
        self.list_arg = None

        if args:
            for arg in args.split(','):
                t, name = arg.split()
                self.args.append((t, name))
                if 'List' in t:
                    self.list_arg = name

        self.sqls = []

    def add_sql(self, line):
        self.sqls.append(line)

    def __str__(self):
        return '%s %s (%s)\n%s\n' % (
            self.resp, self.name, ','.join(['%s %s' % t for t in self.args]), '\n'.join(self.sqls))

    @property
    def resp(self):
        resp = convert_to_java_type(self.raw_resp)

        # map<userId,list<UserEdu>>， 需要查处 userId的类型
        if 'map' in self.raw_resp:
            bean = self.get_bean(resp)

            # map<userId,list<UserEdu>> => userId,list<UserEdu>
            b = re.search('<(.+)>', self.raw_resp).group(1)
            key = b.split(',')[0].strip()

            for s in self.api.structs:
                if s.name != bean:
                    continue

                for f in s.fields_rs:
                    if f.name == key:
                        t = f.type
                        t = {'int': 'Integer', 'long': 'Long'}.get(t, t)
                        resp = resp.replace(key, t)
        return resp

    # 用于future
    @property
    def resp_obj(self):
        r = self.resp
        m = {'int': 'Integer', 'long': 'Long'}
        return m.get(r, r)

    @property
    def group_key(self):
        resp = convert_to_java_type(self.raw_resp)

        # map<userId,list<UserEdu>>， 需要查处 userId的类型
        if 'map' in self.raw_resp:
            bean = self.get_bean(resp)

            # map<userId,list<UserEdu>> => userId,list<UserEdu>
            b = re.search('<(.+)>', self.raw_resp).group(1)
            key = b.split(',')[0].strip()
            return key

    @property
    def sql(self):
        # sql = ' '.join(self.sqls)
        # sql = sql.replace(r'\s+', ' ')

        sql, args = parse_sqls(self.sqls, self.args)
        return sql

    @property
    def sql_args(self):
        sql, args = parse_sqls(self.sqls, self.args)
        return args

    @property
    def resp_is_list(self):
        return 'list' in self.resp.lower()

    @property
    def is_primitive(self):
        m = dict([(l.lower(), r) for l, r in METHODS.items()])
        if self.resp.lower() in m:
            return m[self.resp.lower()]
        else:
            return ''

            # if self.resp.lower() in [l.lower() for l in METHODS.keys()]:
            #
            # return ''

    @property
    def is_group_py(self):
        r = self.resp.lower()
        return ',' in r and 'map' in r

    # 两种情况，一种是成为一个map， by pk， 第二种是变为一个 list， group by a key
    @property
    def is_group_by_list(self):
        return self.is_group_py and 'list' in self.resp.lower()

    @property
    def has_resp(self):
        return 'void' not in self.resp.lower()

    @property
    def generate_id(self):
        return 'insert' in self.sql.lower() and 'int' in self.resp.lower()

    @property
    def update_insert(self):
        return 'update ' in self.sql.lower() or 'insert ' in self.sql.lower()

    def get_bean(self, data):
        # list<>
        b = re.search('<(.+)>', data).group(1)
        if ',' in b:
            # 这里有两种情况，
            # 1: 一情况看是group_by, map<userId,list<UserEdu>>
            if '<' in b:
                return re.search('<(.+)>', b).group(1)
            else:
                # 2. 第二种是把list变为map，map<useID, GeekInfo>
                return b.split(',')[1].strip()

        else:
            return b

    @property
    def resp_bean(self):
        if self.resp_is_list:
            return self.get_bean(self.resp)
        elif self.is_group_py:
            return self.get_bean(self.resp)
        else:
            return self.resp


class DbApi(object):
    def __init__(self):
        self.namespace = ''
        self.structs = []
        self.funcs = []


# FUNC_START, FUNC_MID, FUNC_END, STRUCT_START, STRUCT_MID, STRUCT_END = range(6)

IN_FUNC, IN_STRUCT, OTHER = range(3)


def parse_file(f):
    dbapi = DbApi()
    state = OTHER

    for line in open(f, 'r'):
        # clean and remove comment
        for com in ['//', '--', "#"]:
            idx = line.find(com)
            if idx >= 0:
                line = line[:idx]
            line = line.strip()

        if not line:
            continue

        if 'namespace' in line:
            dbapi.namespace = line.split()[-1]
            continue

        if line.startswith(STRUCT):
            state = IN_STRUCT
            struct = Struct(line, dbapi)
        elif line.startswith(FUNC):
            state = IN_FUNC
            func = Func(line, dbapi)
        elif line == '}':
            if state == IN_FUNC:
                dbapi.funcs.append(func)
            elif state == IN_STRUCT:
                dbapi.structs.append(struct)
            state = OTHER
        else:
            if state == IN_FUNC:
                func.add_sql(line)
            elif state == IN_STRUCT:
                struct.add_field(line)

    loader = template.Loader(DIR, autoescape=None)

    folder = dbapi.namespace.replace('.', '/')

    def write_to_file(name, data):
        f = '%s/%s/%s.java' % (ARGS.out, folder, name)
        if not os.path.isdir(os.path.dirname(f)):
            os.makedirs(os.path.dirname(f))
        data = data.decode("utf-8")
        open(f, 'w').write(data)

    for bean in dbapi.structs:
        java = loader.load('bean.tpl').generate(bean=bean, ns=dbapi.namespace)
        write_to_file(bean.name, java)

    java = loader.load('api.tpl').generate(funcs=dbapi.funcs, ns=dbapi.namespace)
    write_to_file("DBApi", java)

    if ARGS.test:
        java = loader.load('api_test.tpl').generate(funcs=dbapi.funcs, ns=dbapi.namespace)
        write_to_file("DBApiTest", java)


if __name__ == '__main__':
    parse_file(ARGS.input)
