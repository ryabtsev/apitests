import itertools
import json
import time
import hashlib
from copy import deepcopy
from urllib.parse import (
    parse_qs,
    urlparse,
)

from apitests.contrib.gemini import get_payload
from apitests.stub import (
    MockResponse,
    MockResponseAsync,
    Stubs,
)

__all__ = (
    'CONTEXT_COMBINATION_INDEX',
    'INITIAL_COMBINATION_INDEX',
    'StubsGen',
    'StubsGenMixin',
)


CONTEXT_COMBINATION_INDEX = 0
INITIAL_COMBINATION_INDEX = 1


class StubsGenMixin:
    iterations = 2
    iteration_combinations = []

    def __init__(
        self, data, initial_points=None, contexts=None,
        assert_requests=False, prefill_data_used=False,
        skip_gen_doublerun=False, external_services={}
    ):
        super().__init__(data, assert_requests=assert_requests, external_services=external_services)
        self.skip_gen_doublerun = skip_gen_doublerun
        self.passed_combinations = []
        self.data_used = {}
        self.generated_pipeline = []
        self.stub_combination = None
        self.paths_indexes = {}

        self.iteration = 0

        self.initial_points = initial_points
        self.contexts = contexts

        if prefill_data_used:
            self.data_used = data

        self.reload_combination()

    def reload_combination(self):
        self.get_paths_indexes()
        self.sizes = self.get_sizes()
        self.combination_iter = itertools.product(*[list(range(n))for n in self.sizes])
        self.stubs_size = len(self.sizes)

    def init_test(self):
        self.generated_pipeline = []

        if self.iteration == 0:
            combination = self.get_stub_combination()

            if combination:
                pass
            elif self.iteration_combinations:
                time.sleep(1)
                self.iteration = 1
                combination = self.iteration_combinations.pop(0)
            else:
                combination = None
        elif self.iteration_combinations:
            combination = self.iteration_combinations.pop(0)
        else:
            combination = None

        self.stub_combination = combination

    @property
    def combination_prompt(self):
        return [
            list(self.data[service][path])[self.stub_combination[index]].split('-')[-1]
            for (service, path, ), index in self.paths_indexes.items()
            if self.stub_combination[index]
        ]

    @property
    def combination_prompt_full(self):
        return [
            list(self.data[service][path])[self.stub_combination[index]].split('-')[-1]
            for (service, path, ), index in self.paths_indexes.items()
        ]

    @property
    def default_prompt(self):
        return [
            str(list(self.data[service][path])[0]).split('-')[-1]
            for (service, path, ), index in self.paths_indexes.items()
        ]

    def append_external_api(self, service, method, path, pattern, status,
                            data=None, content=None, params=None, prompt=None):
        pd = {
            '_point': 'external_api',
            '_context': self.context,
            '_service': service,
            'method': method,
            'path': path,
            'status': status,
            'content': deepcopy(content),
        }
        if pattern and path != pattern:
            pd['pattern'] = pattern
        if data:
            pd['data'] = data
        if params:
            pd['params'] = params
        if prompt:
            pd['prompt'] = prompt
        self.generated_pipeline.append(pd)

        if self.extend_through_test_case:
            self.test_case.extend_pipeline([pd])

    def get_sizes(self):
        d = [len(self.contexts), len(self.initial_points)]
        d += [None for i in range(len(self.paths_indexes.items()))]
        for service in self.data_used:
            for mp, val in self.data_used[service].items():
                d[self.paths_indexes[(service, mp,)]] = len(val.keys())
        return d

    def finish_test(self):
        combination = [None for i in range(self.stubs_size)]
        combination[CONTEXT_COMBINATION_INDEX] = self.stub_combination[CONTEXT_COMBINATION_INDEX]
        combination[INITIAL_COMBINATION_INDEX] = self.stub_combination[INITIAL_COMBINATION_INDEX]
        mps = [(
            item['_service'],
            '#'.join([
                item['method'],
                item.get('pattern', item['path'])
            ]),
        ) for item in self.generated_pipeline]
        for service, mp in mps:
            key = (service, mp,)
            index = self.paths_indexes[key]
            value = self.stub_combination[self.paths_indexes[key]]
            combination[index] = value

        self.passed_combinations.append(combination)

        if self.iteration == 0 and not self.skip_gen_doublerun:
            self.iteration_combinations.append(self.stub_combination)

    @property
    def initial_point(self):
        return self.stub_combination[1]

    def get_initial_points(self):
        result = self.stub_combination[1]
        if isinstance(result, list):
            result = [result]
        return deepcopy(result)

    def get_response_index(self, service, mp):
        key = (service, mp,)
        return self.stub_combination[self.paths_indexes[key]]

    def get_paths_indexes(self):
        stubs_start_from = INITIAL_COMBINATION_INDEX + 1
        for service in self.data_used:
            for mp in self.data_used[service]:
                key = (service, mp,)
                if key not in self.paths_indexes:
                    index = len(self.paths_indexes) + stubs_start_from
                    self.paths_indexes[key] = index

    def get_stub_combination(self):
        while True:
            try:
                combo = next(self.combination_iter)
            except StopIteration:
                combo = None
                break

            any_matched = False
            for passed in reversed(self.passed_combinations):
                matched = True
                for i, v in enumerate(passed):
                    if v is not None and combo[i] != v:
                        matched = False
                        break
                if matched:
                    any_matched = True
                    break

            if not any_matched:
                break
        return combo

    @property
    def context(self):
        return self.contexts[self.stub_combination[0]]

    def request(self, method, url, async_mode=False, **kwargs):
        response_class = MockResponseAsync if async_mode else MockResponse
        url = str(url)
        obj = urlparse(url)
        path = obj.path

        params = {}
        for key, param in parse_qs(obj.query).items():
            params[key] = param[0] if len(param) == 1 else param

        service, path = self.get_external_service(url)
        if not service:
            raise NotImplementedError(
                'Request to apidocs (Open API specs) for expanding .apistubs file. '
                'Url: [%s] %s (%s)' % (method, url, kwargs)
            )

        method = method.lower()
        method_pattern = None
        pattern, options = self.get_pattern_data(self.data if self.pipeline else self.data_used, service, path, method=method)
        if not options:
            pattern, options = self.get_pattern_data(self.data, service, path, method=method)
            if options:
                method_pattern = '#'.join([method, pattern])
                self.data_used.setdefault(service, {})
                self.data_used[service][method_pattern] = options
                self.stub_combination += (0, )
                self.reload_combination()

        if not options:
            self.requests_patcher.stop()
            payload = get_payload(method.upper(), url, )
            self.requests_patcher.start()
            if payload is None:
                raise NotImplementedError(
                    'Extend apistubs.yaml file.\n'
                    'Prompt example fro LLM (Gemini) includind internal RAG or/and MCPs:\n'
                    'Suggest response for http request: '
                    '[%s] %s' % (method.upper(), url, )
                )
            else:
                method_pattern = '#'.join([method, path])
                key = hashlib.sha256(method_pattern.encode('utf-8')).hexdigest()[:10]
                options = {
                    '200-ok_' + key: payload,
                    '404-not_found_' + key: {},
                    '500-error_' + key: {},
                }
                self.data_used.setdefault(service, {})
                self.data_used[service][method_pattern] = options
                self.stub_combination += (0, )
                self.reload_combination()
        
        if method_pattern is None:
            method_pattern = '#'.join([method, pattern])

        index = self.get_response_index(service, method_pattern)
        cases = list(options.keys())
        content_key = cases[index]
        status = int(content_key.split('-')[0])
        prompt = content_key.split('-')[1]
        content = options[content_key]

        respose = response_class(status, json.dumps(content))

        if 'params' in kwargs and kwargs['params']:
            params.update(kwargs['params'])

        data = kwargs.get('data')
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass

        self.append_external_api(
            service, method, path, pattern, status,
            data=data, params=params or None, content=content,
            prompt=prompt
        )

        return respose


class StubsGen(StubsGenMixin, Stubs):
    pass
