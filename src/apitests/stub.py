"""
Active Stubs handler based on APIStubs notations

It uses multi libraries patched methods behind opentelemetry wrappers.
Real opentelemetry traces are produced through tests running.
"""

import json
from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import (
    parse_qs,
    urlparse,
)

import requests
import yaml

from .utils import (
    force_bytes,
    select_path,
)

try:
    from httpcore import Response as HTTPCoreResponse
except ImportError:
    HTTP_CORE_ENABLED = False
else:
    HTTP_CORE_ENABLED = True

try:
    import aiohttp
except ImportError:
    AIOHTTP_ENABLED = False
else:
    AIOHTTP_ENABLED = True


__all__ = (
    'MockResponse',
    'Stubs',
)


class MockResponse(requests.Response):
    def __init__(self, status_code, content):
        super().__init__()
        self.status_code = int(status_code)
        self._content = force_bytes(content)

    async def read(self):
        return self._content

    def release(self):
        pass

    @property
    def status(self):
        return self.status_code


class MockResponseAsync(MockResponse):
    async def json(self, *args, **keargs):
        return json.loads(self._content)


class StubsFileMixin:
    @classmethod
    def config(cls, path):
        data = cls.load_from_file(path)
        data.pop('apistubs', None)
        cls.clear_nodes(data)
        return data or {}

    @classmethod
    def load_from_file(cls, path):
        with open(path) as points_file:
            data = points_file.read()
            return yaml.load(data, Loader=yaml.Loader)

    @classmethod
    def clear_nodes(cls, data, dep=0):
        # clear commented nodes ("_ ...")
        if dep == 3:
            return
        if not data:
            return

        remove_apps = []
        for app in data:
            if isinstance(app, str) and app[0] == '_':
                remove_apps.append(app)
            cls.clear_nodes(data[app], dep=dep + 1)

        for app in remove_apps:
            data.pop(app)


class Stubs(StubsFileMixin):
    def __init__(
        self,
        data=None,
        expexted_points=None,
        assert_requests=False,
        external_services=None
    ):
        self.is_gentests = True
        self.data = data
        self.expexted_points = expexted_points
    
        self.assert_requests = assert_requests

        self.prompt = None
        self.pipeline = None
        self.extend_through_test_case = False

        self.external_services = external_services or {}

    @staticmethod
    def get_pattern_data(data, service, path, method=None):
        extra = None
        paths = [mp.split('#')[1] for mp in data.get(service, {})]
        pattern = select_path(paths, path)
        if method and pattern:
            mp = f'{method}#{pattern}'
            extra = data[service].get(mp)
        return pattern, extra

    def select_response(self, options):
        content_key = None
        for key in options:
            if not content_key:
                content_key = key
            stub_alias = key.split('-')[1]
            if stub_alias in self.prompt:
                content_key = key
                self.prompt.remove(stub_alias)
        content = options[content_key]
        status = int(content_key.split('-')[0])
        return status, content

    @contextmanager
    def patch_aiohttp(self):
        if not AIOHTTP_ENABLED:
            yield
        else:
            with patch('aiohttp.ClientSession._request', wraps=self.request_async):
                yield

    @contextmanager
    def patch_httpcore(self):
        if not HTTP_CORE_ENABLED:
            yield
        else:
            with patch(
                'httpcore._sync.connection_pool.ConnectionPool.handle_request',
                wraps=self.httpcore_handle_request
            ):
                yield

    @contextmanager
    def patch_requests(self):
        # parallel gemini requests
        self.requests_patcher = patch('requests.adapters.HTTPAdapter.send', wraps=self.send)
        self.requests_patcher.start()
        yield
        self.requests_patcher.stop()
        # with patch('requests.adapters.HTTPAdapter.send', wraps=self.send) as self.requests_patcher:
        #   yield

    @contextmanager
    def up(
        self, pipeline=None, assert_requests=False, prompt=None,
        test_case=None, extend_through_test_case=False
    ):
        self.pipeline = pipeline
        self.assert_requests = assert_requests
        self.prompt = prompt

        self.test_case = test_case
        self.extend_through_test_case = extend_through_test_case

        if self.pipeline:
            for point in self.pipeline.points:
                if point.name == 'external_api':
                    point.pattern, _ = self.get_pattern_data(
                        self.data, point.service, point.path, method=point.method
                    )
                    point.called = False

        if self.is_gentests:
            with self.patch_requests():
                with self.patch_aiohttp():
                    with self.patch_httpcore():
                        yield
        else:
            with patch('requests.api.request', wraps=self.request) as mock_request:
                with patch('requests.Session.request', wraps=self.request):
                    yield mock_request

    def find_point(self, points, service, method, path):
        result = None
        for point in points:
            if point.method != method or point.service != service:
                continue
            if point.path == path:
                return point

        return result

    def get_external_service(self, url):
        obj = urlparse(str(url))
        path = obj.netloc + obj.path
        for name in self.external_services:
            if name and path.startswith(name):
                return (
                    self.external_services.get(name),
                    path[len(name):] if obj.netloc else path
                )
        return None, None

    def send(self, request, **kwargs):
        data = request.body
        if data:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = parse_qs(request.body)
                data = self.normalize_query(data)

        url = request.url
        params = parse_qs(urlparse(url).query)
        params = self.normalize_query(params)
        method = request.method
        options = {
            'data': data or None,
            'headers': request.headers,
            'params': params or None,
        }
        return self.request(method, url, **options)

    @staticmethod
    def to_str(value):
        if value is None or not isinstance(value, int):
            return value
        try:
            value = str(value)
        except ValueError:
            return value
        return value

    def normalize_query(self, expected):
        if isinstance(expected, dict):
            expected = expected.copy()
            for key in expected:
                value = expected[key]
                if not isinstance(expected[key], list):
                    if value is not None:
                        expected[key] = self.to_str(value)
                elif not len(expected[key]):
                    expected[key] = None
                elif len(expected[key]) == 1:
                    expected[key] = self.to_str(value[0])
                else:
                    expected[key] = list(map(str, expected[key]))
            expected = {k: v for k, v in expected.items() if v is not None}
        return expected

    def assertEqualData(self, point, **kwargs):
        data = kwargs['data']
        expected = point.data

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass

        if kwargs.get('headers', {}).get('Content-Type') == 'application/x-www-form-urlencoded':
            expected = self.normalize_query(expected)
            data = self.normalize_query(data)

        self.test_case.assertEqual(data, expected, 'Unxpected request data. Point %s' % point.raw)

    def assertEqualParams(self, point, **kwargs):
        expected = self.normalize_query(point.params)
        params = self.normalize_query(kwargs.get('params'))
        self.test_case.assertEqual(
            params, expected,
            'Unexpected request params. Point %s' % point.raw
        )

    def httpcore_handle_request(self, request):
        data = request.stream._stream.decode()
        if data:
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                data = parse_qs(data)
        url = str(request.url.origin) + request.url.target.decode()
        params = parse_qs(urlparse(url).query)
        method = request.method.decode()
        options = {
            'data': data or None,
            'headers': {k.decode(): v.decode() for k, v in request.headers},
            'params': params or None,
        }
        response = self.request(method, url, **options)
        return HTTPCoreResponse(response.status_code, headers={}, content=response.content)

    def request_async(self, method, url, **kwargs):
        return self.request(method, url, async_mode=True, **kwargs)

    def request(self, method, url, async_mode=False, **kwargs):
        response_class = MockResponseAsync if async_mode else MockResponse
        method = method.lower()
        service, path = self.get_external_service(url)
        if service:
            if self.expexted_points:
                point = self.find_point(self.expexted_points, service, method, path)
                if point:
                    if point.data is not None:
                        self.test_case.assertEqual(
                            kwargs['data'], point.data,
                            'Unxpected request data. Point %s' % point.raw
                        )
                    return response_class(
                        point.response_status,
                        json.dumps(point.response_content)
                    )

            if self.pipeline:
                pattern, options = self.get_pattern_data(self.data, service, path, method=method)
                if options:
                    status, content, point = self.pipeline.get_reponse(service, method, pattern)
                    if point:
                        self.assertEqualData(point, **kwargs)
                        self.assertEqualParams(point, **kwargs)
                        self.test_case.assertDictContainsSubset(
                            point.headers or {}, kwargs.get('headers', {}),
                            'Unxpected request headers. Point %s' % point.raw
                        )
                    if status is None:
                        status, content = self.select_response(options)

                    return response_class(status, json.dumps(content or {}))

        raise NotImplementedError(
            f'Unexpected api call.\nService ({service}), method ({method}), path ({path})\n'
        )
