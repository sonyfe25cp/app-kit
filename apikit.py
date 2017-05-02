import os
import re
import argparse

from tornado import template
from datetime import datetime

parser = argparse.ArgumentParser(description="Generate Android, iOS REST API from definition file.")
parser.add_argument('--api', type=str, default='', help='API definition file')
parser.add_argument('--ns', type=str, default='-', help='Namespace, override in the definition file')
parser.add_argument('--dir', type=str, default="", help='output directory to put the generated code')
parser.add_argument('--context', type=str, default="", help='URL context, like /api /apiv2')
parser.add_argument('--lang', type=str, default='', help='android, servlet')

OPTIONS = parser.parse_args()

DIR = os.path.abspath(os.path.dirname(__file__))

PRIMITIVES = {
    'i32': 0, 'i64': 0, 'float32': 0, 'float64': 0, 'string': '""', 'bool': 'false', 'object': 'null'
}

JAVA_TYPE_MAPPING = [
    ('list<i32>', 'List<Integer>'),
    ('list<', 'List<'),
    ('i32', 'int'),
    ('object', 'Object'),
    ('i64', 'long'),
    ('float32', 'float'),
    ('float64', 'double'),
    ('bool', 'boolean'),
    ('string', 'String'),
    ('datetime', 'Timestamp')
]

SWIFT_TYPE_MAPPING = [
    ('i32', 'Int'),
    ('i64', 'Int'),
    ('float32', 'Double'),
    ('float64', 'Double'),
    ('bool', 'Bool'),
    ('string', 'String'),
]

OBJC_TYPE_MAPPING = [
    ('i32', 'int '),
    ('i64', 'long '),
    ('float32', 'double '),
    ('float64', 'float '),
    ('bool', 'bool '),
    ('string', 'NSString *'),
]


def first_lower(s):
    return s[0].lower() + s[1:]


def convert_to_java_type(t):
    for k, v in JAVA_TYPE_MAPPING:
        t = t.replace(k, v)

    return t


def convert_to_swift_type(t):
    for k, v in SWIFT_TYPE_MAPPING:
        t = t.replace(k, v)

    if 'list' in t:
        t = t.replace('list<', '[')
        t = t.replace('>', ']')

    return t


def convert_to_objc_type(t):
    for k, v in OBJC_TYPE_MAPPING:
        if k == t:
            return v

    if 'list' in t:
        return 'NSMutableArray *'
    return '%s *' % t


class Arg(object):
    def __init__(self, type, name, api, optional=False, default=None):
        self.t = type
        self.name = name
        self.api = api
        self.optional = optional
        self.default_ = default


    @property
    def is_primitive(self):
        return self.t in PRIMITIVES

    @property
    def list(self):
        return self.t.startswith('list')

    @property
    def list_item(self):
        return Arg(self.t[len('list<'):-1], '', self.api)

    def type(self, lang, e=None):
        "convert to language type"
        if lang == 'java':
            return convert_to_java_type(self.t)
        elif lang == 'swift':
            return convert_to_swift_type(self.t)
        elif lang == 'objc':
            ob = convert_to_objc_type(self.t)
            if e:  # for objective c
                if '*' in ob:
                    ob = ob[:-2]
            return ob

    def default(self, lang):
        if lang == 'swift':
            if self.default_ is not None:
                return self.default_
            if self.t == "string":
                return '""'
            if self.is_primitive:
                return 0
            if 'list' in self.t:
                return "[]"
            return "%s()" % self.t
        elif lang == 'java' or lang == 'objc':
            return self.default_

    def null(self, lang):
        if lang == 'java':
            if self.t in ['i32', 'i64', 'float32', 'float64']:
                return 0
            else:
                return "null"

    @property
    def is_defined(self):
        if self.is_primitive or self.bean or (self.list and self.list_item.is_defined):
            return True
        return False

    @property
    def bean(self):
        for b in self.api.structs:
            if b.name == self.t:
                return b
        else:
            return False


class Bean(object):
    def __init__(self, api, name):
        self.api = api  # reference whole api
        self.name = name
        self.fields = []

    def add_field(self, line):
        optional = 'optional' in line
        line = line.replace('optional', '')
        default = None
        if '=' in line:
            line, default = line.split('=')
            default = default.strip(',;').strip()

        line = line.strip(',;').strip()
        if len(line.split()) == 2:
            t, n = line.split()
            self.fields.append(Arg(t.strip(), n.strip(), self.api, optional, default))

    @property
    def requires(self):
        return [f for f in self.fields if not f.optional]

    @property
    def optionals(self):
        return [f for f in self.fields if f.optional]

    def __str__(self):
        return '%s: %s' % (self.name, self.fields)


class Batch(object):
    def __init__(self, api, line, annotations):
        self.api = api
        self.annotations = annotations

        m = re.search('(.+)\s*\((.+)\)', line)
        if m and len(m.groups()) == 2:
            self.name, funcs = m.groups()
            self.funcs = [f.strip() for f in funcs.split(',')]

    def func(self, name):
        f = [f for f in self.api.funcs if f.name == name]
        return f[0] if f else None

    @property
    def params(self):
        r = []
        for fn in self.funcs:
            f = self.func(fn)
            r.append((
                f,
                Arg(f.params[0].t, first_lower('%sReq' % fn), self.api),
                Arg(f.ret.t, first_lower('%sResp' % fn), self.api),
            ))
        return r

    @property
    def uri(self):
        for a in self.annotations:
            if a.name == 'url':
                return a.params


class Func(object):
    def __init__(self, api, line, annotations):
        self.api = api
        self.annotations = annotations

        m = re.search('(.+)\s+(.+)\s*\((.*)\)', line)
        self.name, self.ret, self.params = None, None, []
        if m and len(m.groups()) == 3:
            self.ret, self.name, params = m.groups()
            self.ret = Arg(self.ret, '', api)  # with type info

            if ',' in params:
                params = params.split(',')
            else:
                params = [params]

            for p in params:
                if len(p.split()) == 2:
                    self.params.append(p.split())

            self.params = [Arg(t, n, self.api) for t, n in self.params]  # with type info

    def __str__(self):
        return '%s %s(%s)' % (self.name, self.ret, ', '.join('%s %s' % p for p in self.params))

    @property
    def url(self):
        for a in self.annotations:
            if a.name == 'url':
                url = a.params
                idx = url.find('?')
                if idx > 0:
                    return url[:idx], url[idx + 1:]
                return url, ''

    @property
    def uri(self):
        u, qs = self.url
        return self.api.context + u

    def concat_url(self, lang):
        all_args = {}  # arg name => identifier
        for arg in self.params:
            if arg.is_primitive:
                all_args[arg.name] = arg
            else:
                t = arg.bean
                if t:
                    for f in t.fields:
                        all_args[f.name] = Arg(f.t, "%s.%s" % (arg.name, f.name), self.api)

        def encode(var, type):
            if 'string' in type.t:
                if lang == 'java':
                    return 'URLEncoder.encode(%s == null ? "" : %s, "utf8")' % (var, var)
                elif lang == 'swift':
                    return var
                elif lang == 'objc':
                    return '[self encode:%s]' % var
                    # return "%s.stringByAddingPercentEncodingWithAllowedCharacters(.URLQueryAllowedCharacterSet)" % var
            else:
                return var

        objc_vars = []
        objc_formats = {'i32': '%d', 'i64': '%l', 'string': '%@', 'float32': '%f', 'bool': '%d', 'float64': '%f'}

        def repl(m):
            t = all_args[m.group(1)]
            del all_args[m.group(1)]
            if lang == 'java':
                return '" + ' + encode(m.group(1), t) + ' + "'
            elif lang == 'swift':
                return "\(%s)" % m.group(1)
            elif lang == 'objc':
                objc_vars.append(encode(m.group(1), t))
                return objc_formats[t.t]

        if lang == 'java':
            r = '"%s"' % re.sub(":(\\w+)", repl, self.uri)
            if self.query:
                r += ' + "?%s"' % re.sub(":(\\w+)", repl, self.query)

            if all_args and self.method == 'GET':
                if not self.query:
                    r = '%s + "?"' % r
                else:
                    r = '%s + "&"' % r

            query_params = ""
            for idx, (name, var) in enumerate(all_args.items()):
                query_params = '%s + "%s=" + %s' % (query_params, name, encode(var.name, var))
                if idx != len(all_args) - 1:
                    query_params += ' + "&"'

            return r, all_args, query_params

        elif lang == 'swift':
            r = re.sub(":(\\w+)", repl, self.uri)
            if self.query:
                r += '?%s' % re.sub(":(\\w+)", repl, self.query)
            if all_args and self.method == "GET":
                if not self.query:
                    r += '?'
                else:
                    r += '&'

            query_params = ''
            for idx, (name, var) in enumerate(all_args.items()):
                query_params += "%s=\(%s)" % (name, encode(var.name, var))
                if idx != len(all_args) - 1:
                    query_params += '&'

            return r, all_args, query_params

        elif lang == "objc":
            r = re.sub(":(\\w+)", repl, self.uri)
            if self.query:
                r += '?%s' % re.sub(":(\\w+)", repl, self.query)

            if all_args and self.method == 'GET':
                r += '&' if self.query else '?'

            query, params = "", []
            for idx, (name, var) in enumerate(all_args.items()):
                if idx > 0:
                    query += '&'
                query += '%s=%s' % (name, objc_formats[var.t])
                params.append(encode(var.name, var))

            if self.method == "GET":
                r += query
                objc_vars += params

            return r, objc_vars, (query, params)

    @property
    def query(self):
        u, qs = self.url
        return qs

    @property
    def method(self):
        for a in self.annotations:
            if a.name.lower() in ['get', 'post', 'delete']:
                return a.name.upper()

        return 'GET'


class Annotation(object):
    def __init__(self, line):
        if '(' not in line:
            self.name = line
            self.ps = None
        else:
            m = re.search('(.+)\((.+)\)', line)
            self.name, self.ps = None, None
            if m:
                groups = m.groups()
                if len(groups) > 0:
                    self.name = m.group(1)

                if len(groups) > 1:
                    ps = groups[1]
                    if ',' in ps:
                        self.params = dict(p.split('=') for p in ps.split(','))
                    else:
                        self.params = ps

    def __str__(self):
        return '%s: %s' % (self.name, self.ps)


class Api(object):
    def __init__(self, ns):
        self.ts = datetime.now()
        self.ns = ns
        self.structs = []
        self.funcs = []
        self.context = OPTIONS.context
        self.batches = []

    def replace_name(self, n, ns, names):
        if 'list' in n and n[len('list<'):-1] in names:
            return 'list<%s%s>' % (ns, n[len('list<'):-1])
        if n in names:
            return '%s%s' % (ns, n)
        return n

    # objective-c does not support ns
    def prefix_ns(self):
        ns = self.ns
        names = set(b.name for b in self.structs)
        for b in self.structs:
            b.name = self.replace_name(b.name, ns, names)
            for f in b.fields:
                f.t = self.replace_name(f.t, ns, names)

        # for b in self.batches:
        # b.name = '%s%s' % (ns, b.name)

        for f in self.funcs:
            f.ret.t = self.replace_name(f.ret.t, ns, names)
            for p in f.params:
                p.t = self.replace_name(p.t, ns, names)

    def process_batch(self):
        for b in self.batches:
            resp = Bean(self, '%sResp' % b.name)
            req = Bean(self, '%sReq' % b.name)
            for fn, inp, out in b.params:
                resp.fields.append(Arg(out.t, out.name, self))
                req.fields.append(Arg(inp.t, inp.name, self))
            self.structs.append(resp)
            self.structs.append(req)

    def check_valid(self):
        for s in self.structs:
            for f in s.fields:
                if not f.is_defined:
                    print 'ERROR, "%s" is not a type, in struct %s' % (f.t, s.name)
                    return False

        for f in self.funcs:
            if not f.ret.is_defined:
                print 'ERROR, return value of %s "%s" is not a type' % (f.name, f.ret.t)
                return False
            for p in f.params:
                if not p.is_defined:
                    print 'ERROR, param of %s "%s" is not a type' % (f.name, p.t)
                    return False

        for b in self.batches:
            for name in b.funcs:
                f = b.func(name)
                if not f:
                    print 'ERROR, In batch %s, "%s" is not defined.' % (b.name, name)
                    return False
                if f.method != 'GET':
                    print 'ERROR, In batch %s, %s: only batch get is supported.' % (b.name, f.name)
                    return False

                if len(f.params) > 1:
                    print "ERROR, In batch %s, %s has %d params, only support 1 param" % (b.name, f.name, len(f.params))
                    return False

        return True


def _remove_comment(line):
    idx = line.find('//')
    if idx >= 0:
        line = line[:idx]
    return line.strip()


def _parse_file(f):
    api, annotations, struct = Api(''), [], None

    for idx, line in enumerate(open(f).readlines()):
        line = _remove_comment(line)
        if not line:
            continue

        if line.startswith('ns'):
            api.ns = line[2:].strip()
            continue

        if line.startswith('struct'):
            struct = Bean(api, line[len('struct'):].strip(' {'))
            continue

        if line[0] == '@':
            annotations.append(Annotation(line[1:]))
            continue

        if line.startswith('func'):
            api.funcs.append(Func(api, line[len('func'):].strip(), annotations))
            annotations = []  # clear
            continue

        if line.startswith('batch'):
            api.batches.append(Batch(api, line[len('batch'):].strip(), annotations))
            annotations = []  # clear
            continue

        if '}' in line:
            api.structs.append(struct)
            struct = None
            continue

        if struct:
            struct.add_field(line)

    if OPTIONS.ns != '-':  # pass from command line, has higher priority
        api.ns = OPTIONS.ns

    # if api.check_valid():

    return api


def write_to_file(f, data):
    if not os.path.isdir(os.path.dirname(f)):
        os.makedirs(os.path.dirname(f))

    # data = re.sub("\n+", "\n", data)
    data = re.sub("\{\n+", "{\n", data)
    open(f, 'w').write(data)


def write_servlet(api):
    folder = api.ns.replace('.', '/')

    loader = template.Loader('%s/tmpls/servlet' % DIR, autoescape=None)

    for bean in api.structs:
        java = loader.load('bean.tpl').generate(bean=bean, api=api)
        write_to_file('%s/%s/%s.java' % (OPTIONS.dir, folder, bean.name), java)

    for tmpl, r in [('handler', 'IHandler'), ('dispatcher', 'Dispatcher'), ('context', 'Context')]:
        code = loader.load(tmpl + '.tpl').generate(api=api, funcs=api.funcs)
        write_to_file('%s/%s/%s.java' % (OPTIONS.dir, folder, r), code)


def write_android(api):
    folder = api.ns.replace('.', '/')

    loader = template.Loader('%s/tmpls/android' % (DIR,), autoescape=None)

    java = loader.load('utils.tpl').generate(api=api)
    write_to_file('%s/%s/Utils.java' % (OPTIONS.dir, folder), java)

    for bean in api.structs:
        java = loader.load('bean.tpl').generate(bean=bean, api=api)
        write_to_file('%s/%s/%s.java' % (OPTIONS.dir, folder, bean.name), java)

    java = loader.load('api.tpl').generate(funcs=api.funcs, api=api)
    write_to_file('%s/%s/Api.java' % (OPTIONS.dir, folder), java)


def write_swift(api):
    folder = api.ns.replace('.', '/')
    loader = template.Loader('%s/tmpls/swift' % (DIR,), autoescape=None)
    java = loader.load('beans.tpl').generate(api=api)
    write_to_file('%s/%s/Beans.swift' % (OPTIONS.dir, folder), java)

    java = loader.load('api.tpl').generate(api=api)
    write_to_file('%s/%s/Api.swift' % (OPTIONS.dir, folder), java)


def write_objective_c(api):
    loader = template.Loader('%s/tmpls/objc' % (DIR,), autoescape=None)
    for tmpl, r in [('Api.h.tpl', 'Api.h'), ('Api.m.tpl', 'Api.m'), ('Beans.h.tpl', 'Beans.h'),
                    ('Beans.m.tpl', 'Beans.m')]:
        r = '%s%s' % (api.ns, r)
        code = loader.load(tmpl).generate(api=api)
        write_to_file('%s/%s' % (OPTIONS.dir, r), code)


def write_js(api):
    loader = template.Loader('%s/tmpls/js' % (DIR,), autoescape=None)
    for tmpl, r in [('api.tpl', 'api.js')]:
        r = '%s%s' % (api.ns, r)
        code = loader.load(tmpl).generate(api=api)
        write_to_file('%s/%s' % (OPTIONS.dir, r), code)


def main():
    if not OPTIONS.api or not OPTIONS.lang:
        parser.print_usage()
        print 'ERROR: --api and --lang is missing, which are required'
        return

    api = _parse_file(OPTIONS.api)
    if not api.check_valid():
        return

    api.process_batch()

    if OPTIONS.lang == 'servlet':
        write_servlet(api)
    elif OPTIONS.lang == 'android':
        write_android(api)
    elif OPTIONS.lang == 'swift':
        write_swift(api)
    elif OPTIONS.lang == 'js':
        write_js(api)
    elif OPTIONS.lang == 'objc':
        api.prefix_ns()
        write_objective_c(api)


# python apikit.py --api demo/test.api --lang a --dir /tmp/src
def run_tests():
    import os

    DIR = os.path.abspath(os.path.dirname(__file__))
    r = _parse_file('%s/demo/test.api' % DIR)

    assert r.ns == 'com.kanzhun.api' or r.ns == OPTIONS.ns
    assert r.check_valid()

    r.process_batch()

    assert len(r.funcs) == 2
    assert r.funcs[0].name == 'AutoComplete'
    assert r.funcs[0].url == ('/ac/:kind', 'q=:q')
    assert len(r.structs) == 8
    assert r.structs[0].name == 'User'
    assert len(r.structs[0].fields) == 3
    assert 'id' in r.structs[0].fields[0].name
    assert Arg("list<Salary>", "", None).list_item.t == "Salary"

    assert len(r.batches) == 1
    b = r.batches[0]
    assert b.name == 'Batch'
    assert b.funcs == ['SearchSalary', 'AutoComplete']


if __name__ == '__main__':
    run_tests()
    main()
