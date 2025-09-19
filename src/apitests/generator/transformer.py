
import copy
import hashlib
import json
from unittest.mock import ANY

from apitests.generator.generalizer import (
    clean_not_serializable,
    generalize_snapshot_by_double_run,
    set_pattern,
)

__all__ = (
    'fold_pipeline',
    'unfold_pipeline',
    'get_flows',
    'remove_meta',
    'set_test_any',
)


def get_color(index):
    data = str(json.dumps(index)).encode('utf-8')
    m = hashlib.shake_256()
    m.update(data)
    return m.hexdigest(20)


INDEX_PARTS = [
    '_point',
    'exchange',
    'routing_key',
    'service',
    'pattern',
    'method',
    'status',
    'content',
    'data',
]


def normilize_pipeline(data, data_repeated=None, clean_method=None, use_set_pattern=True):
    data = clean_not_serializable(data)
    if data_repeated:
        data_repeated = clean_not_serializable(data_repeated)

    for test, item in data.items():
        for point_index, point in enumerate(item):
            if data_repeated:
                point_repeated = data_repeated[test][point_index]

            if 'status' in point and point['status'] is None:
                point['status'] = 0
                if data_repeated:
                    point_repeated['status'] = 0

            point.setdefault('_meta', {})
            point['_meta'].update({
                'test': test,
            })

            if data_repeated:
                point_repeated.setdefault('_meta', {})
                point_repeated['_meta'].update({
                    'test': test,
                })

            origin_point = copy.deepcopy(point)
            if use_set_pattern:
                set_pattern(point)
            if clean_method:
                clean_method(point)
            point['_meta'].pop('trace', None)

            if data_repeated:
                if use_set_pattern:
                    set_pattern(point_repeated)
                if clean_method:
                    clean_method(point_repeated)
                point_repeated['_meta'].pop('trace', None)
                generalize_snapshot_by_double_run(point, point_repeated)

            index = []
            for key in INDEX_PARTS:
                if key == 'content' and 'content' in point:
                    index.append(json.dumps(point[key]))
                elif key == 'data':
                    if point['_point'] in ['worker', 'notification', 'configuration', 'api']:
                        index.append(json.dumps(point.get(key)))
                elif key in point:
                    index.append(point[key])
                elif key == 'pattern' and 'path' in point:
                    index.append(point['path'])

            point['hash'] = get_color(index)
            origin_point['hash'] = point['hash']

            point['_meta'] = {
                'index': tuple(index),
                'origin': origin_point,
                'test': test,
            }

    def sort_key(item):
        index = ()
        for point in item[1]:
            index += point['_meta']['index']
        return index

    return {k: v for k, v in sorted(data.items(), key=sort_key)}


def merge_configuration(entries):
    conf = entries[0]
    for entry in entries:
        for setting in entry['data']:
            if setting not in conf['data']:
                conf['data'][setting] = entry['data'][setting]

    return conf


def normalize_configurations(data):
    for item in data:
        new_entries = []
        conf_entries = []
        log_entries = []
        logs_count = len([entry for entry in item['entries'] if entry['_point'] == 'log'])
        for entry in item['entries']:
            if entry['_point'] == 'configuration':
                conf_entries.append(entry)
            elif entry['_point'] == 'log' and len(log_entries) < logs_count - 1:
                log_entries.append(entry)
            else:
                new_entries.append(entry)
        if conf_entries:
            new_entries.insert(0, merge_configuration(conf_entries))
        item['entries'] = new_entries


class HashedPoint(str):
    def __new__(cls, point):
        value = point.copy()
        value.pop('_meta', None)
        key = json.dumps(value)
        obj = str.__new__(cls, key)
        obj.payload = point
        return obj


def hashable_pipeline(data):
    hashable_set = []

    for item in data.values():
        entries = []
        for point in item:
            entries.append(HashedPoint(point))
        hashable_set.append(entries)
    return hashable_set


def unfold_pipeline(tree, deepcopy=False):
    pipelines = {}
    for index, flow in enumerate(get_flows(tree), start=1):
        pipeline = load_flow(tree, flow)
        if deepcopy:
            pipeline = copy.deepcopy(pipeline)
        pipelines['TEST.%s' % str(1000 + index)[1:]] = pipeline

    return pipelines


def fold_pipeline(data):
    data = hashable_pipeline(data)
    tree = {}

    for item in data:
        cursor = tree
        for point in item:
            cursor.setdefault((point, ), {})
            cursor = cursor[(point, )]

    def reduce_tree(tree):
        for key in list(tree.keys()):
            reduce_tree(tree[key])
            sub_keys = list(tree[key].keys())
            if len(sub_keys) == 1:
                sub_key = sub_keys[0]
                tree[key + sub_key] = tree[key][sub_key]
                tree.pop(key)

    def transform_tree(tree, index=()):
        data = {}
        for i, key in enumerate(tree.keys(), start=1):
            item_index = index + (i,)

            item = []
            for point in key:
                point.payload.setdefault('_meta', {})
                point.payload['_meta']['branch'] = '.'.join([str(i) for i in item_index])
                item.append(point.payload)

            children = transform_tree(tree[key], item_index)
            if children:
                item.append(children)

            name = [str(i) for i in item_index]
            data['WORKFLOW-w%s' % '.'.join(name)] = item

        return data

    reduce_tree(tree)
    return transform_tree(tree)


def get_flows(tree):
    flows = []
    if not tree:
        return flows

    for key in tree:
        sub_flows = None
        for point in tree[key]:
            if '_point' not in point:
                sub_flows = get_flows(point)
                if sub_flows:
                    for sub_flow in sub_flows:
                        flows.append([key] + sub_flow)
                else:
                    flows.append([key])
        if sub_flows is None:
            flows.append([key])

    return flows


def load_flow(data, flow):
    def collapse(data, dep=0):
        result = []
        for item in data:
            if '_point' in item:
                result.append(item.copy())
            else:
                key = flow[dep]
                value = item[key]

                result.extend(
                    collapse(value, dep + 1)
                )
        return result
    return collapse(data[flow[0]], dep=1)


def remove_meta(tree):
    points = {}
    if not isinstance(tree, dict):
        return

    for key in tree:
        for point in tree[key]:
            if '_point' not in point:
                points.update(
                    remove_meta(point)
                )
            else:
                origin = point.pop('_meta', {}).get('origin')
                if 'pattern' in point:
                    origin['_meta']['pattern'] = point['pattern']
                key = 'POINT.%s' % point['hash']
                if key not in points:
                    points[key] = origin
                    points[key]['_meta'].setdefault('tests', [points[key]['_meta']['test']])
                else:
                    points[key]['_meta']['tests'].append(origin['_meta']['test'])

    return points


def set_test_any(value):
    if isinstance(value, str) and value == 'ANY':
        return ANY

    if isinstance(value, list):
        for i, v in enumerate(value):
            value[i] = set_test_any(v)
    elif isinstance(value, tuple):
        value = list(value)
        for i, v in enumerate(value):
            value[i] = set_test_any(v)
        value = tuple(value)
    elif isinstance(value, dict):
        for k in value.keys():
            value[k] = set_test_any(value[k])

    return value
