import pytest

from apitests.base import GenTestCase

from .context import ContextsMixin

@pytest.mark.generator
class TestExample(ContextsMixin, GenTestCase):
    feature = 'example'

