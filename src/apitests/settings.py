import sys

try:
    from django.conf import settings
except ImportError:
    IS_DJANGO_STACK = False
else:
    IS_DJANGO_STACK = settings.configured


__all__ = (
    'IS_DJANGO_STACK',
    'EXTERNALS',
    'TRACING_SERVICES',
    'STUBS_HOST',
    'AUTOGEN_MAX_TESTS',
    'PROJECT',
    'GENERATOR_MODE',
)

AUTOGEN_MAX_TESTS = 100

TRACING_SERVICES = []

STAGING_PATH = None

EXTERNALS = {}

PROJECT = None
LOG_DIR = None

STUBS_HOST = None

if IS_DJANGO_STACK:
    from django.conf import settings as app_settings
    PROJECT = app_settings.PROJECT
    LOG_DIR = app_settings.LOG_DIR  # type: ignore[misc]


EXTERNALS.update({
    'graph.microsoft.com': 'graphmicrosoft',
    'graph.facebook.com': 'facebook',
})


GENERATOR_MODE = (
    '--tag=generator' in sys.argv or
    '-m=generator' in sys.argv
)

OPENTELEMETRY_ENABLED = False
