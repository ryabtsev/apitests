"""
Base TestCase classes:
GenTestCase - for generator;
WorkflowTestCase - for handle generated tests.
"""

import os
import sys

from . import settings
from .mixins import WorkflowTestCaseMixin

__all__ = (
    'GenTestCase',
    'WorkflowTestCaseMixin',
    'WorkflowTestCase',
)


if settings.IS_DJANGO_STACK:
    from django.test import TestCase
else:
    from unittest import TestCase  # type: ignore[assignment]


GENERATOR_VERSION = None

try:
    from apitests.generator import GenerativeTestCaseMixin as BaseGenerativeTestCaseMixin
except ImportError:
    if settings.GENERATOR_MODE:
        class BaseGenerativeTestCaseMixin:  # type: ignore[no-redef]
            def test_one(self):
                msg = (
                    '\nInstall generator:\n'
                    '% pip install apitests'
                )
                raise ImportError(msg)
    else:
        class BaseGenerativeTestCaseMixin:  # type: ignore[no-redef]
            pass
else:
    import apitests
    GENERATOR_VERSION = apitests.VERSION
    if settings.GENERATOR_MODE:
        sys.stdout.write(
            '\n\n[ATTENTION] Make sure that installed latest version of generator:\n'
            ' % pip install apitests\n\n'
        )


class GenerativeTestCaseMixin(
    BaseGenerativeTestCaseMixin,
    WorkflowTestCaseMixin,
):
    render_template = os.path.join(os.path.dirname(__file__), 'jinja2/apitests/tests.py.tpl')
    render_template_md = os.path.join(os.path.dirname(__file__), 'jinja2/apitests/tests.rag.md.tpl')
    external_services = settings.EXTERNALS

    render_context = {
        'apitests': __name__.rsplit('.', 1)[0],
        'IS_DJANGO_STACK': settings.IS_DJANGO_STACK,
        'version': GENERATOR_VERSION,
    }

    @classmethod
    def post_process(cls, workflows_tree):
        pass


class GenTestCase(GenerativeTestCaseMixin, TestCase):
    pass


class WorkflowTestCase(WorkflowTestCaseMixin, TestCase):
    pass
