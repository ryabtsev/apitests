"""
Module describetes high-level abstractions for tests

WORKFLOWS DATA MODEL UNDERSTANDABLE FOR BOTH HUMANS AND AI ALIKE

Semantic in priority, tech markers are second.

Key attributes of Workflow Point:
===================================================================================================
Tech/Semantic            | Semantic                                               | Meta          |
===================================================================================================
Role         | Method    | Service | Path           | Request      | Response     | Hash  | Alias |
===================================================================================================
input        | get, post | ACCOUNT | /api/v1/get/   | data: ...    | content: ... |  ...  |  ...  |
output       | patch ... | ABC     | /call/{env}/.. | params: ...  | status: ...  |       |       |
             | mq, kafka | FB      | channel/route  | headers: ... | headers: ... |       |       |
log          | warning   | Live    |                |              |              |       |       |
notification | sms, ...  | Apple   |                |              |              |       |       |
process      | contract  | Steam   |                |              |              |       |       |
context      | ...       |         |                |              |              |       |       |
assert, stub |           |         |                |              |              |       |       |
===================================================================================================

Frozen Points are used for tests from apistubs notation:
```
{service}:
  {method}#{path}:
    {status}-{alias}: {content}
    ...
```
"""

import copy
import json

import yaml

from .settings import OPENTELEMETRY_ENABLED

__all__ = (
    'Workflow',
    'PointApi',
    'PointExternalApi',
    'PointNotification',
    'PointStubAlias',
    'InputMQ',
    'PointMQ',
    'PointLog',
    'PointAssert',
    'ContextSetUp',
    'Process',
)


if OPENTELEMETRY_ENABLED:
    from .serialization.tracer import TestTracer
    tracer = TestTracer()
else:
    tracer = None  # type: ignore[assignment]


class Role:
    INPUT = 'input'
    OUTPUT = 'output'

    ASSERT = 'assert'
    LOG = 'log'
    NOTIFICATION = 'notification'
    PROCESS = 'process'
    CONTEXT = 'context'
    STUB = 'stub'

    INITIALS = [
        INPUT,
        PROCESS,
    ]


class Method:
    # Role: in, out
    # http methods
    GET = 'get'
    POST = 'post'
    DELETE = 'delete'
    PATCH = 'patch'

    HTTP_GROUP = [
        GET, POST, DELETE, PATCH,
    ]

    # others
    MQ = 'mq'
    KAFKA = 'kafka'
    CONTRACT = 'contract'

    # Role: log
    DEBUG = 'debug'
    INFO = 'info'


class Workflow:
    def __init__(self, data, context=None, stubs_data=None, e2e=False):
        self.points = data
        self.context = context
        self.stubs = stubs_data
        self.stubs_modified = False
        self.tracer = tracer
        self.e2e = e2e

    @classmethod
    def load_from_file(cls, path):
        try:
            with open(path) as points_file:
                data = points_file.read()
                return yaml.load(data, Loader=yaml.Loader)
        except FileNotFoundError:
            return {}

    def get_external_calls(self, called=None):
        points = []
        for point in self.points:
            if point.role != Role.OUTPUT or point.method not in Method.HTTP_GROUP:
                continue
            if called is True and not point.called:
                continue
            if called is False and point.called:
                continue

            points.append(point)

        return points

    def get_reponse(self, service, method, pattern, explicit=False):
        for point in self.points:
            if point.role != Role.OUTPUT or point.method not in Method.HTTP_GROUP:
                continue

            if point.called:
                continue

            if (
                point.service != service or
                point.method != method or
                point.pattern != pattern
            ):
                if explicit:
                    raise NotImplementedError(
                        'Invalid point for request '
                        'service (%s), method(%s), pattern (%s).'
                        'point %s' % (service, method, pattern, point.raw)
                    )
                continue

            point.called = True
            return point.response_status, point.response_content, point

        if explicit:
            raise NotImplementedError(
                'PointExternalApi does exist in pipeline: '
                'servise (%s), method(%s), pattern (%s).' % (service, method, pattern,)
            )

        return None, None, None

    @property
    def initials(self):
        return [point for point in self.points if point.role in Role.INITIALS]

    @property
    def initial(self):
        # deprecated
        return self.initials[0] if self.initials else None

    @property
    def stubs_prompt(self):
        return [item.alias for item in self.points if item.role == Role.STUB]


class BasePoint:
    name = 'base'
    role = None  # type: ignore[var-annotated]

    serialize_attrs = {
        'name': '_point',
        'context': '_context',
        'service': '_service',
        'data': 'data',
        'method': 'method',
        'headers': 'headers',
        'path': 'path',
        'pattern': 'pattern',
        'params': 'params',
        'response_status': 'status',
        'response_content': 'content',
        'response_headers': 'response_headers',
        'routing_key': 'routing_key',
        'exchange': 'exchange',
    }
    serialize_attrs_inv = {v: k for k, v in serialize_attrs.items()}

    def __init__(self, **kwargs):
        self.called = False
        self.alias = None
        self.path = ''
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def raw(self):
        result = {}
        for attr in self.serialize_attrs:
            value = getattr(self, attr, None)
            if value:
                if isinstance(value, dict):
                    value = copy.deepcopy(value)
                result[self.serialize_attrs[attr]] = value
        return result

    def to_json(self):
        return json.dumps(self.raw, indent=4)

    @property
    def kwargs(self):
        result = {}
        data = getattr(self, 'data', None)
        params = getattr(self, 'params', None)
        if data:
            result['data'] = data
        if params:
            result['params'] = params
        return result


class PointNotification(BasePoint):
    name = 'notification'
    role = Role.NOTIFICATION

    def __init__(self, data):
        super(PointNotification, self).__init__(data=data)


class PointApi(BasePoint):
    name = 'api'
    role = Role.INPUT

    def __init__(
        self, method, path,
        params=None, data=None,
        headers=None,
        response_status=None, response_content=None, response_headers=None
    ):
        if response_status:
            response_status = int(response_status)

        super(PointApi, self).__init__(
            method=method.lower(), path=path,
            params=params, data=data, headers=headers,
            response_status=response_status, response_content=response_content,
            response_headers=response_headers
        )


class PointExternalApi(BasePoint):
    name = 'external_api'
    role = Role.OUTPUT

    def __init__(
        self, service, method, path,
        params=None, data=None, headers=None,
        response_status=None, response_content=None
    ):
        if response_status:
            response_status = int(response_status)

        super(PointExternalApi, self).__init__(
            service=service,
            method=method.lower(), path=path,
            params=params, data=data, headers=headers,
            response_status=response_status, response_content=response_content
        )


class PointStubAlias(BasePoint):
    name = 'stub_alias'
    role = Role.STUB

    def __init__(self, alias):
        super().__init__(alias=alias)


class InputMQ(BasePoint):
    name = 'input_mq'
    role = Role.INPUT

    def __init__(
        self, data, exchange=None, routing_key=None, headers=None
    ):
        super().__init__(
            method=Method.MQ, path=f'{exchange}/{routing_key}',
            data=data, headers=headers
        )


class PointMQ(BasePoint):
    name = 'mq'
    role = Role.OUTPUT

    def __init__(
        self, data, exchange=None, routing_key=None, headers=None
    ):
        super(PointMQ, self).__init__(
            method=Method.MQ, data=data, headers=headers,
            exchange=exchange, routing_key=routing_key
        )


class PointLog(BasePoint):
    name = 'log'
    role = Role.LOG

    def __init__(self, level, msg, pattern=None):
        super().__init__(
            method=level, path=msg, pattern=pattern
        )


class PointAssert(BasePoint):
    name = 'assert'
    role = Role.ASSERT

    def __init__(self, path):
        super().__init__(path=path)


class ContextSetUp(BasePoint):
    name = 'context'
    role = Role.CONTEXT

    def __init__(self, path):
        super().__init__(path=path)


class Process(BasePoint):
    name = 'process'
    role = Role.PROCESS

    def __init__(self, path):
        super().__init__(path=path)
