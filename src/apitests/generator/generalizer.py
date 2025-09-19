import json
import re

from apitests.helpers import deepdiff

__all__ = (
    'set_pattern',
    'generalize_snapshot_by_double_run',
    'clean_not_serializable',
    'set_any',
)


def set_pattern(point):
    """
    DODO: remake placeholder handling acording OpenAPI specification
    """
    if 'path' not in point or 'pattern' in point:
        return

    path = point['path']
    pattern = path
    pattern = re.sub(r'/(?P<token>\w{32})/', '/{token}/', pattern)
    pattern = re.sub(r'\d{10}', '{token}', pattern)
    if pattern != path:
        point['pattern'] = pattern
        point.pop('path')


def clean_not_serializable(value):
    data = json.dumps(value, default=lambda o: 'ANY')
    return json.loads(data)


def generalize_snapshot_by_double_run(snapshot, snapshot_repeated):
    ddiff = deepdiff(snapshot, snapshot_repeated)
    snapshot_generalized = snapshot
    for p in ddiff.affected_paths:
        path = p[5:-1].split('][')
        value = snapshot_generalized
        for i, key in enumerate(path):
            pk = key[1:-1] if key[0] == "'" else int(key)
            if i + 1 == len(path):
                value[pk] = 'ANY'
            else:
                value = value[pk]


def set_any(data, *args, remove=False):
    if not data:
        return None

    attr = data
    attr_dict = None
    attr_arg = None
    for index, arg in enumerate(args):
        if attr is None:
            return None

        if isinstance(attr, list):
            for d in attr:
                set_any(d, *args[index:], remove=remove)

        if not isinstance(attr, dict):
            return None

        if arg == '*':
            for key in attr:
                set_any(attr[key], *args[index+1:], remove=remove)
            return None

        if arg in attr:
            attr_dict = attr
            attr_arg = arg
            attr = attr[arg]
        else:
            return None

    attr_dict[attr_arg] = 'ANY'

    if remove:
        attr_dict.pop(attr_arg)

    return attr
