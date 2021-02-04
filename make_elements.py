#!/usr/bin/env python3
#
# A primitive script to parse lua_api.txt for formspec elements.
# This script needs Python 3.8+ and ruamel.yaml to work.
#

import copy, json, lua_dump, os, re, ruamel.yaml, urllib.request

def _make_known(**kwargs):
    known = {}
    for k, v in kwargs.items():
        for i in v:
            known[i] = k
    return known

_known = _make_known(
    number=('x', 'y', 'w', 'h', 'selected_idx', 'version',
            'starting_item_index', 'scroll_factor', 'frame_count',
            'frame_duration', 'frame_start'),
    boolean=('auto_clip', 'fixed_size', 'transparent', 'draw_border', 'bool',
             'fullscreen', 'noclip', 'drawborder', 'selected', 'force',
             'close_on_enter'),
    table=('param', 'opt', 'prop'),
    null=('',),
)

def _get_name(n):
    if not isinstance(n, tuple) or n[1] == '...':
        return '...'
    return n[0][:-1].rsplit('_', 1)[0].rstrip('_')

_aliases = {
    'type': 'elem_type',
    'cell': 'cells',
}

def _fix_param_name(param):
    param = param.lower().strip().strip('<>').replace(' ', '_')
    param = _aliases.get(param, param)
    assert param != '...'
    return param

def _fix_param(param):
    if isinstance(param, str):
        if ',' not in param:
            param = _fix_param_name(param)
            return (param, _known.get(param, 'string'))
        param = param.split(',')

    res = []
    for p in map(str.strip, param):
        if p != '...':
            res.append(_fix_param(p))
            continue
        assert res

        last = res.pop()
        # Workaround
        if res and last and isinstance(last, list) and \
                last[0][0].endswith('2') and isinstance(res[-1], list) and \
                res[-1] and res[-1][0][0].endswith('1'):
            last = res.pop()
            last[0] = (last[0][0][:-2], last[0][1])

        name = _get_name(last)
        if name == '...':
            res.append((last, '...'))
        else:
            while res and _get_name(res[-1]) == name:
                res.pop()
            res.append((_fix_param(name), '...'))
        break

    return res

_hooks = {}
def hook(name):
    def add_hook(func):
        _hooks[name] = func
        return func
    return add_hook

# Fix background9
@hook('background9')
def _background9_hook(params):
    assert params[-1] == ('middle', 'string')
    params[-1] = param = []
    param.append(('middle_x', 'number'))
    yield params
    param.append(('middle_y', 'number'))
    yield params
    param.append(('middle_x2', 'number'))
    param.append(('middle_y2', 'number'))
    yield params

# Fix bgcolor
@hook('bgcolor')
def _bgcolor_hook(params):
    yield params
    for i in range(1, len(params)):
        yield params[:-i]

# Fix size
@hook('size')
def _size_hook(params):
    yield params
    yield [[('w', 'number'), ('h', 'number')]]

# Fix style and style_type
@hook('style')
@hook('style_type')
def _style_hook(params):
    # This is not used when parsing but keeps backwards compatibility when
    # unparsing.
    params[0] = [('name', 'string')]
    yield params

    params[0] = [(('selectors', 'string'), '...')]
    yield params

# Fix dropdown
@hook('dropdown')
def _scroll_container_hook(params):
    if isinstance(params[1][0], str):
        params[1] = [('w', 'number'), ('h', 'number')]
    else:
        params[1] = ('w', 'number')
    yield params[:5]
    yield params

# Fix textlist
@hook('textlist')
def _textlist_hook(params):
    if len(params) > 5:
        yield params[:5]
    yield params

_param_re = re.compile(r'^\* `([^`]+)`(?: and `([^`]+)`)?:? ')
def _raw_parse(data):
    # Get everything from the elements heading to the end of the next heading
    data = data.split('\nElements\n--------\n', 1)[-1].split('\n----', 1)[0]

    # Remove the next heading
    data = data.rsplit('\n', 1)[0]

    # Get element data
    for elem_data in data.split('\n### '):
        lines = elem_data.split('\n')
        raw_elem = lines.pop(0)
        if not raw_elem.startswith('`') or not raw_elem.endswith('`'):
            continue

        name, params = raw_elem[1:-2].split('[', 1)
        if params:
            params = _fix_param(params.split(';'))
        else:
            params = []

        if name in _hooks:
            for p in reversed(tuple(map(copy.deepcopy, _hooks[name](params)))):
                yield name, p
            continue

        # Optional parameters
        optional_params = set()
        for line in lines:
            match = _param_re.match(line)
            if not match or 'optional' not in line.lower():
                continue

            optional_params.add(_fix_param_name(match.group(1)))
            if p2 := match.group(2):
                optional_params.add(_fix_param_name(p2))

        # if optional_params:
        #     print('Optional', name, optional_params)

        # Convert the optional parameters into a format formspec_ast can
        # understand without major changes
        while True:
            yield name, params

            if not params:
                break
            last_param = params[-1]
            if (not isinstance(last_param, tuple) or
                    not isinstance(last_param[0], str) or
                    last_param[0] not in optional_params):
                break
            # print('Optional', name, last_param)
            params = params[:-1]

def parse(data):
    """
    Returns a dict:
    {
        'element_name': [
            ['param1', 'param2'],
            ['alternate_params'],
        ]
    }
    """
    res = {}
    for k, v in _raw_parse(data):
        if k not in res:
            res[k] = []
        res[k].append(v)

    for v in res.values():
        v.sort(key=len, reverse=True)

    return res

# TODO: Fix model[] parsing then switch this back to the master branch
URL = 'https://github.com/minetest/minetest/raw/050964b/doc/lua_api.txt'
def fetch_and_parse(*, url=URL):
    with urllib.request.urlopen(url) as f:
        raw = f.read()
    return parse(raw.decode('utf-8', 'replace'))

_comment = """
--
-- Formspec elements list. Do not update this by hand, it is auto-generated
-- by make_elements.py.
--

"""

_yaml_comment = """
#
# This file is automatically generated by make_elements.py and isn't actually
# used by formspec_ast, however it is useful for comparing changes across
# lua_api versions.
#

"""

def main():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'elements.lua')
    data = fetch_and_parse()

    # Horrible code to create elements.yaml
    filename2 = os.path.join(dirname, 'elements.yaml')
    print('Writing to ' + filename2 + '...')
    with open(filename2, 'w') as f:
        f.write(_yaml_comment.lstrip())
        # Yuck - Unparsing then re-parsing the data as JSON is the easiest way
        # I can think of to convert tuples to lists.
        ruamel.yaml.dump(json.loads(json.dumps(data)), f)

    print('Writing to ' + filename + '...')
    with open(filename, 'w') as f:
        f.write(_comment.lstrip())
        f.write(lua_dump.serialize(data))
        # elems = fetch_and_parse()
        # for elem in sorted(elems):
        #     for def_ in elems[elem]:
        #         f.write('formspec_ast.register_element({}, {})\n'.format(
        #             lua_dump.dump(elem), lua_dump.dump(def_)
        #         ))
    print('Done.')

if __name__ == '__main__':
    main()
