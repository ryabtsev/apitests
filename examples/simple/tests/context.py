import os

from apitests import points
from apitests.base import WorkflowTestCaseMixin
from app import main


__all__ = (
    'ContextsMixin',
)


class ContextsMixin(WorkflowTestCaseMixin):
    stubs = os.path.join(os.path.dirname(__file__), 'apistubs.yaml')

    initials = [points.Process('handle')]
    feature = 'cool'
    def handle(workflow, initial):
        main()
