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

    def test_0_ok_ok(self):
        self.run_workflow([
            points.ContextSetUp(self.context_default),
            points.Process(self.handle),
            points.PointExternalApi(
                service='github', method='get', path='/',
            ),
            points.PointStubAlias('ok'),
            points.PointLog('Level 5:charset_normalizer', 'override steps (5) and chunk_size (512) as content does not fit (2 byte(s) given) parameters.'),
            points.PointLog('Level 5:charset_normalizer', 'Trying to detect encoding from a tiny portion of (2) byte(s).'),
            points.PointLog('Level 5:charset_normalizer', 'ascii passed initial chaos probing. Mean measured chaos is 0.000000 %'),
            points.PointLog('Level 5:charset_normalizer', 'ascii should target any language(s) of ["Latin Based"]'),
            points.PointLog('DEBUG:charset_normalizer', 'Encoding detection: ascii is most likely the one.'),
        ])
