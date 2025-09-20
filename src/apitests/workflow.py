"""
Generic workflow handler

Test workflows are flexible.
It can be modified run time to imitate of mocked consumer.
"""

from contextlib import contextmanager

from . import points
from .settings import EXTERNALS
from .stub import Stubs

__all__ = (
    'WorkflowHandlerMixin',
)


class WorkflowHandlerMixin:
    stubs = None  # type: ignore[var-annotated]
    stubs_class = Stubs
    stubs_instance: Stubs = None  # type: ignore[assignment]
    contexts = ['context_default']
    initials: list = []

    external_services = EXTERNALS

    @contextmanager
    def context_default(self, *args, **kwds):
        yield

    @property
    def test_name(self):
        return (
            f'{self.__class__.__module__}.'
            f'{self.__class__.__qualname__}.'
            f'{self._testMethodName}'  # type: ignore[attr-defined]
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # type: ignore[misc]
        if cls.stubs:
            cls.stubs_instance = cls.stubs_class(
                data=cls.stubs_class.config(cls.stubs),
                external_services=cls.external_services
            )

    def setUp(self):
        super().setUp()  # type: ignore[misc]
        self.expexted_points = []
        self.requests_mocked = False
        self.generator_mode = False

    def add_expected_points(self, points, clear=False):
        if clear:
            self.expexted_points.clear()
        self.expexted_points.extend(points)

    def use_context(self, context, workflow):
        if not isinstance(context, str):
            return context(workflow)
        return getattr(self, context)(workflow)

    @contextmanager
    def patch_requests(self, mocked_requests=[]):
        if self.stubs_instance:
            if mocked_requests:
                self.stubs_instance.mocked_requests.extend(mocked_requests)
        else:
            self.stubs_instance = Stubs(
                expexted_points=self.expexted_points,
                mocked_requests=mocked_requests,
                external_services=self.external_services
            )
        if self.requests_mocked:
            yield
        else:
            self.stubs_instance.is_gentests = False
            with self.stubs_instance.up(test_case=self) as mock_request:
                self.requests_mocked = True
                yield mock_request
                self.requests_mocked = False

    def is_e2e_mode(self):
        return False
    
    def is_telemetry_mode(self):
        return False    
    
    def run_workflow(self, workflow=None):
        if not workflow:
            workflow = []

        context = self.contexts[0]
        for item in workflow:
            if item.role == points.Role.CONTEXT:
                context = item.path

        workflow = points.Workflow(
            workflow, context=context, stubs_data=self.stubs_instance.data,
            e2e=self.is_e2e_mode()  # type: ignore[attr-defined]
        )

        self.run_test(workflow)

    def make(self, test, workflow, prompt, context):
        if workflow:
            self.run_test(workflow)
        else:
            self.generator_mode = True
            self.generate_test()

    @contextmanager
    def context_common(self, workflow):
        yield

    @contextmanager
    def context_run(self, workflow):
        with self.use_context(workflow.context, workflow):
            with self.context_common(workflow):
                with self.stubs_instance.up(
                    pipeline=workflow, assert_requests=True,
                    prompt=workflow.stubs_prompt, test_case=self
                ):
                    yield

    @contextmanager
    def context_generator(self, context, workflow):
        with self.use_context(context, workflow):
            with self.context_common(workflow):
                with self.stubs_instance.up(test_case=self, extend_through_test_case=True):
                    yield

    def run_test(self, workflow):
        initials = workflow.initials
        if not initials:
            initials = self.initials[0]
            if not isinstance(initials, list):
                initials = [initials]
            workflow.points.extend(initials)

        with self.context_run(workflow):
            if self.is_telemetry_mode():  # type: ignore[attr-defined]
                if workflow.stubs_modified:
                    self.setUpStubs(stubs=workflow.stubs)  # type: ignore[attr-defined]
                    workflow.stubs_modified = False
                self.setUpStubsAliases(workflow.stubs_prompt)  # type: ignore[attr-defined]

            if workflow.tracer:
                workflow.tracer.start()

            for initial in initials:
                method = getattr(self, self.get_process_method_name(initial))
                response = method(workflow, initial)
                for key in response:
                    setattr(initial, initial.serialize_attrs_inv[key], response[key])

            if workflow.tracer:
                workflow.tracer.log(self.test_name)

    def generate_test(self):
        self.stubs_instance.init_test()  # type: ignore[attr-defined]
        if self.stubs_instance.stub_combination is None:  # type: ignore[attr-defined]
            self.stop_generator()  # type: ignore[attr-defined]
            return

        initials = self.get_initial_points()  # type: ignore[attr-defined]
        initials_original = self.get_initial_points()  # type: ignore[attr-defined]
        workflow = points.Workflow([], stubs_data=self.stubs_instance.data)
        workflow.points.extend(initials)
        self.context = self.stubs_instance.context  # type: ignore[attr-defined]
        with self.context_generator(
            self.stubs_instance.context, workflow  # type: ignore[attr-defined]
        ):
            if workflow.tracer:
                workflow.tracer.start()

            for i, initial in enumerate(initials):
                original = initials_original[i].raw
                self.extend_pipeline([original])  # type: ignore[attr-defined]
                method = getattr(self, self.get_process_method_name(initial))
                response = method(workflow, initial)
                original.update(response)
                for key in response:
                    setattr(initial, initial.serialize_attrs_inv[key], response[key])

            if workflow.tracer:
                content = workflow.tracer.log(self.test_name, save=False)
                self.workflow_meta['trace'] = content  # type: ignore[attr-defined]

        self.stubs_instance.finish_test()  # type: ignore[attr-defined]

    def procces_custom(self, workflow, initial):
        process_method = initial.path
        if isinstance(process_method, str):
            process_method = getattr(self, initial.path)
        process_method(workflow)
        return {}

    @staticmethod
    def get_process_method_name(point):
        if point.role == points.Role.PROCESS:
            return 'procces_custom'

        if point.method in points.Method.HTTP_GROUP:
            return 'process_http_api'

        return None
