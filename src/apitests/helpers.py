import requests
import yaml
from apitests.utils import search

try:
    import requests_mock as base_requests_mock
except ImportError:
    base_requests_mock = None

try:
    from deepdiff import DeepDiff as deepdiff
except ImportError:
    deepdiff = None

try:
    from jinja2 import Environment, BaseLoader
except ImportError:
    Environment = None
    BaseLoader = None

try:
    import uncurl
except ImportError:
    uncurl = None


__all__ = (
    'select_path',
    'curl_to_request',
    'setting_list',
    'requests_mock',
    'deepdiff',
    'uncurl_parse',
    'uncurl_parse_context',
    'render_string',
    'yaml_loads',
    'yaml_dumps',
)


def requests_mock():
    if base_requests_mock is None:
        raise NotImplementedError

    return base_requests_mock.Mocker()


def uncurl_parse(curl):
    return uncurl.parse(curl)


def uncurl_parse_context(curl):
    return uncurl.parse_context(curl)


def render_string(val, context={}):
    template = Environment(loader=BaseLoader).from_string(val)
    return template.render(**context)


def yaml_loads(data):
    return yaml.load(data, Loader=yaml.Loader)


def yaml_dumps(data, **options):
    return yaml.safe_dump(data, **options)


def select_path(paths, path):
    max_path_size = 0
    result = None
    for path_pattern in paths:
        if path_pattern == path:
            return path_pattern

        if search(path_pattern, path) and len(path_pattern) > max_path_size:
            result = path_pattern
            max_path_size = len(path_pattern)

    return result


def request_point(point, base_url=None, session=None):
    point_raw = point.raw
    url = point_raw['path']
    headers = {}
    for key, value in point_raw.get('headers', {}).items():
        if isinstance(value, int):
            headers[key] = str(value)
        elif isinstance(value, (str, bytes,)):
            headers[key] = value

    point_raw = point.raw
    if not session:
        session = requests

    response = session.request(
        point_raw['method'], url, params=point_raw.get('query'),
        data=point_raw.get('data'), headers=headers
    )
    return response


def curl_to_request(curl, indent=0):
    entry = uncurl_parse(curl)
    entry = '\n'.join([' ' * indent + i for i in entry.split('\n')]).strip()
    return entry


def setting_list(value):
    value = [i.strip() for i in value.strip().replace('\n', ' ').replace(',', ' ').split(' ')]
    return [i for i in value if i]
