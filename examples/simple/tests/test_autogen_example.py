from unittest.mock import ANY

import pytest

from unittest import TestCase

from apitests import points

from simple.tests.context import ContextsMixin

__all__ = (
    'AutoGenTestExample',
)


class AutoGenTestExample(
    ContextsMixin,
    TestCase
):
    apitests = '0.0.1'

    def test_smoke(self):
        self.run_workflow()

    def test_0_ok_ok_7583741b24(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointExternalApi(
                service='github', method='get', path='/',
            ),
            points.PointStubAlias('ok_7583741b24'),
        ])

    def test_1_ok_not_found_7583741b24(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('not_found_7583741b24'),
        ])

    def test_2_error_error_7583741b24(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('error_7583741b24'),
        ])
