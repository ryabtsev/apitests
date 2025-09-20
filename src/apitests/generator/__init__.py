import copy
import inspect
import os
import sys
from contextlib import contextmanager
from importlib import import_module
from unittest.case import strclass

import yaml
from apitests import (
    VERSION,
    points,
    settings,
)
from apitests.generator.stubgen import StubsGenMixin
from apitests.generator.transformer import (
    fold_pipeline,
    get_flows,
    load_flow,
    normilize_pipeline,
    remove_meta,
    set_test_any,
)
from apitests.helpers import (
    render_string,
    yaml_dumps,
)
from apitests.serialization.arazzo import build_workflows
from apitests.serialization.visual import render_table


__all__ = (
    'generative_test_standalone',
    'render_tests',
    'GenerativeTestCaseMixin',
)


def render_tests(context, render_template):
    with open(render_template) as points_file:
        data = points_file.read()

    output = render_string(data, context)

    output = output.replace("'ANY'", 'ANY')
    return output


def generative_test_standalone(max_tests=None, snapshots=None, regenerate=True, run=True, feature=None):
    base_path = os.path.dirname(inspect.getfile(inspect.currentframe().f_back))
    snapshots = os.path.join(base_path, f'{feature}.apiflows.yaml')

    pipelines = []
    if regenerate:
        if max_tests is None:
            max_tests = settings.AUTOGEN_MAX_TESTS
        max_tests *= 2
        pipelines += [('generated', None, None, None,) for test in range(max_tests)]

    if run:
        pipelines += expand_tests(snapshots)

    return pipelines


def build_pipeline(pipeline_raw):
    test_points = []
    context = None
    pipeline_raw = set_test_any(pipeline_raw)

    for item in pipeline_raw:
        if item['_point'] == 'api':
            point = points.PointApi(
                item['method'], item['path'],
                params=item.get('params'), data=item.get('data'), headers=item.get('headers'),
                response_status=item['status'], response_content=item.get('content')
            )
        if item['_point'] == 'external_api':
            point = points.PointExternalApi(
                item['_service'], item['method'], item['path'],
                params=None, data=item.get('data'),
                response_status=item['status'], response_content=item.get('content')
            )

        test_points.append(point)

        if '_context' in item:
            context = item['_context']

    pipeline = points.Workflow(test_points, context=context)
    pipeline.load_flow()
    return pipeline


def filter_asserts(pipeline_raw, used_asserts, used_hashes):
    pipeline = []
    for item in pipeline_raw:
        if item['hash'] not in used_hashes:
            item['is_used_hash'] = False
            used_hashes.append(item['hash'])
        else:
            item['is_used_hash'] = True

        is_used = False
        if item['_point'] in [points.PointExternalApi.name]:
            # TODO: refactoring
            if 'path' not in item:
                is_used = True
            elif (item['method'], item['path'],) in used_asserts:
                is_used = True
            else:
                used_asserts.append((item['method'], item['path'],))
        item['is_used'] = is_used
        pipeline.append(item)
    return pipeline


def expand_tests(
    pipelines_raw,
    build=True,
    filter_used_asserts=False,
    filter_used_subflows=False,
    context_set_up=False
):
    tree = points.Workflow.load_from_file(pipelines_raw)
    pipelines = []
    used_asserts = []
    used_hashes = []
    success_no = 1

    for flow in get_flows(tree):
        pipeline = load_flow(tree, flow)
        name = ''
        context = None
        prompt = []
        meta = {
            'success': True,
        }
        for item in pipeline:
            if '_context' in item and item['_context']:
                context = item['_context']

            prompt_input = item.get('prompt')
            if prompt_input:
                prompt.append(prompt_input)
                name = prompt_input

        if filter_used_asserts:
            pipeline = filter_asserts(pipeline, used_asserts, used_hashes)

        if build:
            pipeline = build_pipeline(pipeline)

        if (
            not filter_used_subflows or
            not all([item['is_used_hash'] for item in pipeline])
        ):
            if context_set_up:
                pipeline.insert(0, {
                    '_point': 'context',
                    'path': context,
                })
            meta['success'] = not any([item.get('status') in [408, 500, 503] for item in pipeline])
            meta['prefix'] = 'ok_' if meta['success'] else 'error_'
            if meta['success']:
                meta['success_no'] = success_no
                success_no += 1
            pipeline[0]['meta'] = meta
            pipelines.append((name, pipeline, prompt, context,))

    return pipelines


class ContextMixin:
    contexts = ['context_default']

    @contextmanager
    def context_empty(self, *args, **kwargs):
        yield

    @contextmanager
    def context_default(self, *args, **kwargs):
        yield

    def copy_initial(self, index):
        initial = self.initials[index]
        return copy.deepcopy(initial)

    def get_initial_points(self):
        index = self.stubs_instance.stub_combination[1]
        initials = self.initials[index]
        if not isinstance(initials, list):
            initials = [initials]
        return copy.deepcopy(initials)


class GenMeta(type):
    def __new__(cls, name, bases, attrs):
        # TODO: improve it
        custom_generator = attrs.get('test_000_generated')

        feature = attrs.get('feature')
        regenerate = attrs.get('regenerate', True)
        # TODO: revise run from .apiflows.yaml
        run = attrs.get('run')
        max_tests = attrs.get('max_tests')

        generator_mode = (
            '--tag=generator' in sys.argv or
            '-m=generator' in sys.argv
        )

        for arg in sys.argv:
            if '.generator' in arg or '.test_generator' in arg:
                generator_mode = True

        if not custom_generator and feature and generator_mode:
            base_path = os.path.dirname(import_module(attrs['__module__']).__file__)
            snapshots = os.path.join(base_path, f'test_autogen_{feature}.apiflows.yaml')
            pipelines = []
            if regenerate:
                if max_tests is None:
                    max_tests = settings.AUTOGEN_MAX_TESTS
                max_tests *= 2
                pipelines += [('generated', None, None, None,) for test in range(max_tests)]

            if run:
                pipelines += expand_tests(snapshots)

            for i, (name, pipeline, prompt, context,) in enumerate(pipelines):
                index = str(1000 + i)[1:]
                attrs[f'test_{index}_{name}'] = lambda self: self.make(name, pipeline, prompt, context)

        return super().__new__(cls, name, bases, attrs)


class GenerativeTestCaseMixin(ContextMixin, metaclass=GenMeta):
    apitests_version = VERSION
    initials = []
    asserts = []
    pipelines = {}
    finished = False

    skip_fold = False

    skip_gen_doublerun = False

    standalone = False
    clean_method = None

    exclude_aliases = None

    render_template = None
    render_template_md = None
    render_context = {}

    @classmethod
    def generator_set_up_class(cls):
        class StubsGen(StubsGenMixin, cls.stubs_class):
            pass

        cls.stubs_instance = StubsGen(
            data=StubsGen.config(cls.stubs),  # exclude_aliases=cls.exclude_aliases
            initial_points=list(cls.initials),
            contexts=list(cls.contexts),
            skip_gen_doublerun=cls.skip_gen_doublerun,
            external_services=cls.external_services,
        )

    @classmethod
    def generator_tear_down_class(cls):
        cls.save_tests()

    def generator_set_up(self):
        self.pipeline = []
        self.context = None

    def generator_tear_down(self):
        if not self.pipeline:
            return
        self.append_pipeline(self.pipeline)

    @classmethod
    def setUpClass(cls):
        super(GenerativeTestCaseMixin, cls).setUpClass()
        cls.generator_set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.generator_tear_down_class()
        super().tearDownClass()

    def setUp(self):
        if self.finished:
            return
        super(GenerativeTestCaseMixin, self).setUp()
        self.generator_set_up()

    def tearDown(self):
        if self.finished:
            return
        super(GenerativeTestCaseMixin, self).tearDown()
        self.generator_tear_down()

    @classmethod
    def stop_generator(cls):
        cls.finished = True

    @classmethod
    def get_base_path(cls):
        return os.path.dirname(os.path.abspath(sys.modules[cls.__module__].__file__))

    @classmethod
    def get_pipeline_spanshots(cls, version=''):
        base_path = cls.get_base_path()
        #base_path = os.path.dirname(os.path.abspath(sys.modules[cls.__module__].__file__))
        snapshots = os.path.join(base_path, f'test_autogen_{cls.feature}{version}.apiflows.yaml')
        return snapshots

    @classmethod
    def get_pipeline_html(cls):
        return '%s.arazzo.html' % cls.get_pipeline_spanshots().replace('.apiflows.yaml', '')

    @classmethod
    def get_pipeline_arazzo(cls):
        return '%s.arazzo.yaml' % cls.get_pipeline_spanshots().replace('.apiflows.yaml', '')

    @classmethod
    def get_pipeline_py(cls):
        # TODO: rewrite
        return '%s.py' % cls.get_pipeline_spanshots().replace('.apiflows.yaml', '')

    @classmethod
    def get_pipeline_rag(cls):
        # TODO: rewrite
        return '%s.rag.md' % cls.get_pipeline_spanshots().replace('.apiflows.yaml', '')

    def append_point(self, point):
        data = point.raw
        data.update({'_context': self.context})
        self.pipeline.append(data)

    def append_asserts(self, *args):
        for method in self.asserts:
            try:
                workflow = args[0] if args else None  # temp: backward compatibility
                getattr(self, method)(workflow)
            except AssertionError:
                pass
            else:
                self.pipeline.append({
                    '_point': 'assert',
                    '_context': self.context,
                    'path': method,
                })

    def extend_pipeline(self, pipeline):
        for point in pipeline:
            point['_context'] = self.context

        self.pipeline.extend(pipeline)

    def append_pipeline(self, pipeline):
        test_name = self._testMethodName
        test_case = strclass(self.__class__)
        test_case = 'TEST'
        key = '%s_%s' % (strclass(self.__class__), self.stubs_instance.iteration,)
        self.pipelines.setdefault(key, [])
        num = str(100 + len(self.pipelines[key]))[1:]
        # 'test_%s_generated' % num
        # print(test_name, 'test_%s_generated' % num)
        # TODO: fix part of name `002``

        name = [
            test_case, '002', 'test_%s_generated' % num,
        ]
        prompt = [point['prompt'] for point in self.pipeline if 'prompt' in point]
        if prompt:
            name = [
                test_case, 'test_%s_generated' % num,
            ]
        self.pipelines[key].append(('.'.join(name), pipeline,))

    def get_pipelines(self):
        key = '%s_%s' % (strclass(self.__class__), self.stubs_instance.iteration,)
        return self.pipelines[key]

    @property
    def workflow_meta(self):
        # TODO: rework
        return self.pipeline[0].setdefault('_meta', {})

    def clean(cls):
        pass

    @classmethod
    def save_tests(cls):
        key = '%s_%s' % (strclass(cls), 0,)
        key_repeated = '%s_%s' % (strclass(cls), 1,)
        data = cls.pipelines.pop(key, {})
        data = dict(data)
        data_repeated = cls.pipelines.pop(key_repeated, {})
        data_repeated = dict(data_repeated)
        if not data:
            return

        if cls.clean_method:
            clean_method = cls.clean_method
        else:
            clean_method = None

        data = normilize_pipeline(
            data, data_repeated=data_repeated,
            clean_method=clean_method, use_set_pattern=False
        )
        if not cls.skip_fold:
            data = fold_pipeline(data)

        os.makedirs(os.path.dirname(cls.get_pipeline_html()), exist_ok=True)
        with open(cls.get_pipeline_html(), 'w') as html_file:
            html_file.write(render_table(data, context={
                'feature': cls.feature,
            }))

        with open(cls.get_pipeline_spanshots('.meta'), 'w') as tests_file:
            tests_file.write(yaml_dumps(data))

        remove_meta(data)

        with open(cls.get_pipeline_spanshots(), 'w') as tests_file:
            tests_file.write(yaml_dumps(data))

        with open(cls.get_pipeline_arazzo(), 'w') as workflows_file:
            workflows_file.write(yaml.dump(build_workflows(data), sort_keys=False))

        cls.post_process(data)

        contexts_mixin = None
        base_path = strclass(cls).rsplit('.', 2)[0]

        for mixin in cls.mro():
            mixin = strclass(mixin)
            if '.context' in mixin:
                contexts_mixin = mixin
                break

        if hasattr(cls, 'worker_class'):
            worker_class_name = strclass(cls.worker_class).rsplit('.', 1)
        else:
            worker_class_name = 'DeafaultWorker'

        pipelines = expand_tests(
            cls.get_pipeline_spanshots(),
            build=False, filter_used_asserts=True,
            context_set_up=True,
            filter_used_subflows=True
        )
        cls.render_context.update({
            'self_class': strclass(cls).rsplit('.', 1),
            'base_path': base_path,
            'worker_class': worker_class_name,
            'contexts_mixin': contexts_mixin.rsplit('.', 1) if contexts_mixin else None,
            'pipelines': pipelines,
            'feature': cls.feature,
        })

        with open(cls.get_pipeline_py(), 'w') as tests_file:
            tests_file.write(render_tests(cls.render_context, cls.render_template))

        with open(cls.get_pipeline_rag(), 'w') as tests_file:
            tests_file.write(render_tests(cls.render_context, cls.render_template_md))

        yaml_dumps(cls.stubs_instance.data_used)
        # TODO: improve approuche 
        print(yaml_dumps(cls.stubs_instance.data_used))

    @classmethod
    def save_artifact(cls, name, data):
        name = name.format(feature=cls.feature)
        with open(os.path.join(cls.get_base_path(), name), 'w') as artifact_file:
            artifact_file.write(data)

    @classmethod
    def post_process(self, workflows_tree):
        pass

    def append_api(self, point):
        # DEPRECATED
        self.pipeline.append({
            '_point': 'api',
            '_context': self.context,
            'method': point.method,
            'path': point.path,
            'data': point.data or {},
            'status': point.response_status,
            'content': point.response_content or {},
            'headers': point.headers,
        })
