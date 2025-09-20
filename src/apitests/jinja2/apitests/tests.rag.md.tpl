# Feature: {{ feature }}

{% for name, pipeline, prompt, context in pipelines %}
{%- if pipeline.0.meta.success or True %}
## Scenario {{ pipeline.0.meta.success_no }}
{%- for item in pipeline %}

{% if item._point == 'api' -%}
{{ loop.index }}. API request {{ item.method }} {{ item.path }} {% if item.params %}with query params: {{ item.params }}{% endif %}

{%- if item.data %}
Request data: {{ item.data }}{% endif %}
{%- if item.headers %}
Request headers: {{ item.headers }}{% endif %}
{%- if item.content %}
Response content: {{ item.content }}{% endif %}
{%- if item.response_headers %}
Response headers: {{ item.response_headers }},{% endif %}
Response status: {{ item.status }}

{% elif item._point == 'input_mq' -%}
{{ loop.index }}. Input MQ (exchange: {{ item.exchange }}, routing_key: {{ item.routing_key }})
Data: {{ item.data }}

{% elif item._point == 'mq' -%}
{{ loop.index }}. MQ (exchange: {{ item.exchange }}, routing_key: {{ item.routing_key }})
exchange='{{ item.exchange }}', routing_key='{{ item.routing_key }}',
Data: {{ item.data }}

{% elif item._point == 'external_api' -%}
{{ loop.index }}. External API request in service "{{ item._service }}" method:{{ item.method }} path:{{ item.path }} {% if item.params %}with query params: {{ item.params }}{% endif %}

{%- if item.data %}
Request data: {{ item.data }}{% endif %}
{%- if item.headers %}
Request headers: {{ item.headers }}{% endif %}
{%- if item.content %}
Response content: {{ item.content }}{% endif %}
{%- if item.response_headers %}
Response headers: {{ item.response_headers }},{% endif %}
Response status: {{ item.status }}

{% elif item._point == 'context' -%}
{{ loop.index }}. Use context "{{ item.path }}"

{% elif item._point == 'process' -%}
{{ loop.index }}. Process operation "{{ item.path }}"

{% elif item._point == 'notification' -%}
{{ loop.index }}. Notification
Data: {{ item.data }}

{% elif item._point == 'log' and item.pattern != 'ANY' -%}
{{ loop.index }}. Log message
{{ item.method }} {% if item.path != 'ANY' and item.path|length < 150 %}{{ item.path }}{% else %}{{ item.pattern }}{% endif %}

{%- endif %}
{%- endfor %}

{%endif -%}
{% endfor %}
