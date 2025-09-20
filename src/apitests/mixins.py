"""
Typical TestCase constructor from `contrib/*` parts
"""

from .contrib.asserts import CustomAssertsCaseMixin
from .contrib.logs import LogsTestCaseMixin
from .settings import IS_DJANGO_STACK
from .workflow import WorkflowHandlerMixin


__all__ = (
    'APITestsMixin',
    'AsyncWorkflowMixin',
    'WorkflowTestCaseMixin',
)


class APITestsMixin(WorkflowHandlerMixin):
    pass


class BaseWorkflowTestCaseMixin(
    CustomAssertsCaseMixin,
    LogsTestCaseMixin,
    WorkflowHandlerMixin
):
    pass


if IS_DJANGO_STACK:
    class DjangoWorkflowTestCaseMixin:
        pass

    class WorkflowTestCaseMixin(
        DjangoWorkflowTestCaseMixin,
        BaseWorkflowTestCaseMixin
    ):
        pass
else:
    class WorkflowTestCaseMixin(BaseWorkflowTestCaseMixin):
        pass


AsyncWorkflowMixin = WorkflowTestCaseMixin
