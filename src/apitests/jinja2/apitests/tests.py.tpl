from unittest.mock import ANY

{% if IS_DJANGO_STACK -%}
from django.test import (
    TestCase,
    tag,
)
{% else -%}
import pytest

from aiohttp.test_utils import AioHTTPTestCase as TestCase
{% endif %}
from gentests.base import points

from {{ contexts_mixin[0] }} import {{ contexts_mixin[1] }}

__all__ = (
    'AutoGen{{ self_class[1] }}',
)


{% if IS_DJANGO_STACK -%}
@tag('e2e', 'telemetry')
{% else -%}
@pytest.mark.e2e
@pytest.mark.telemetry
{% endif -%}
class AutoGen{{ self_class[1] }}(
    {{ contexts_mixin[1] }},
    TestCase
):
    apitests = '{{ version }}'

    def test_smoke(self):
        self.run_workflow()
{% for name, pipeline, prompt, context in pipelines %}
    def test_{{ loop.index0 }}_{{ pipeline.0.meta.prefix }}{{ name }}(self):
        self.run_workflow([
        {%- for item in pipeline %}
        {%- if item._point == 'api' %}
            points.PointApi(
                method='{{ item.method }}', path='{{ item.path }}',
                {%- if item.params %}
                params={{ item.params }},{% endif %}
                {%- if item.data %}
                data={{ item.data }},{% endif %}
                {%- if item.headers %}
                headers={{ item.headers }},{% endif %}
                {%- if item.content %}
                response_content={{ item.content }},{% endif %}
                {%- if item.response_headers %}
                response_headers={{ item.response_headers }},{% endif %}
                response_status={{ item.status }}
            ),
        {%- elif item._point == 'input_mq' %}
            points.InputMQ(
                exchange='{{ item.exchange }}', routing_key='{{ item.routing_key }}',
                {%- if item.data %}
                data={{ item.data }},{% endif %}
                {%- if item.headers %}
                headers={{ item.headers }},{% endif %}
            ),
        {%- elif item._point == 'mq' %}
            points.PointMQ(
                exchange='{{ item.exchange }}', routing_key='{{ item.routing_key }}',
                {%- if item.data %}
                data={{ item.data }},{% endif %}
                {%- if item.headers %}
                headers={{ item.headers }},{% endif %}
            ),
        {%- elif item._point == 'external_api' and not item.is_used %}
            points.PointExternalApi(
                service='{{ item._service }}', method='{{ item.method }}', path='{{ item.path }}',
                {%- if item.params %}
                params={{ item.params }},{% endif %}
                {%- if item.data %}
                data={{ item.data }},{% endif %}
            ),
            points.PointStubAlias('{{ item.prompt }}'),
        {%- elif item._point == 'external_api' %}
            points.PointStubAlias('{{ item.prompt }}'),
        {%- elif item._point == 'assert' %}
            points.PointAssert(self.{{ item.path }}),
        {%- elif item._point == 'context' %}
            points.ContextSetUp(self.{{ item.path }}),
        {%- elif item._point == 'process' %}
            points.Process(self.{{ item.path }}),
        {%- elif item._point == 'notification' %}
            points.PointNotification(
                data={{ item.data }}
            ),
        {%- elif item._point == 'log' and item.pattern != 'ANY' %}
            points.PointLog('{{ item.method }}', '{% if item.path != 'ANY' and item.path|length < 150 %}{{ item.path }}{% else %}{{ item.pattern }}{% endif %}'),
        {%- endif %}
        {%- endfor %}
        ])
{% endfor %}
