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

    def test_0_ok_ok_7583741b24_nationalize(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointExternalApi(
                service='github', method='get', path='/',
            ),
            points.PointStubAlias('ok'),
            points.PointExternalApi(
                service='nationalize', method='post', path='/',
                params={'name': 'kate'},
            ),
            points.PointStubAlias('ok_7583741b24_nationalize'),
        ])

    def test_1_ok_ok_a33f416397_ipinfo(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('ok'),
            points.PointStubAlias('not_found_7583741b24_nationalize'),
            points.PointExternalApi(
                service='ipinfo', method='get', path='/161.185.160.93/geo',
            ),
            points.PointStubAlias('ok_a33f416397_ipinfo'),
        ])

    def test_2_ok_not_found_a33f416397_ipinfo(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('ok'),
            points.PointStubAlias('not_found_7583741b24_nationalize'),
            points.PointStubAlias('not_found_a33f416397_ipinfo'),
        ])

    def test_3_error_error_a33f416397_ipinfo(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('ok'),
            points.PointStubAlias('not_found_7583741b24_nationalize'),
            points.PointStubAlias('error_a33f416397_ipinfo'),
        ])

    def test_4_error_error_7583741b24_nationalize(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('ok'),
            points.PointStubAlias('error_7583741b24_nationalize'),
        ])

    def test_5_ok_ok_7583741b24_nationalize(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('not_found'),
            points.PointStubAlias('ok_7583741b24_nationalize'),
        ])

    def test_6_error_ok_7583741b24_nationalize(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointStubAlias('error'),
            points.PointStubAlias('ok_7583741b24_nationalize'),
        ])
