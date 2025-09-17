import datetime
from decimal import Decimal

from parse import Parser

__all__ = (
    'select_path',
    'is_protected_type',
    'force_bytes',
)


_PROTECTED_TYPES = (
    type(None), int, float, Decimal, datetime.datetime, datetime.date, datetime.time,
)


class ExtendedParser(Parser):
    def _handle_field(self, field):
        # handle as path parameter field
        field = field[1:-1]
        path_parameter_field = "{%s:PathParameter}" % field
        return super()._handle_field(path_parameter_field)


class PathParameter:
    name = "PathParameter"
    pattern = r"[^\/]+"

    def __call__(self, text):
        return text


parse_path_parameter = PathParameter()


def search(path_pattern, full_url_pattern):
    extra_types = {parse_path_parameter.name: parse_path_parameter}
    p = ExtendedParser(path_pattern, extra_types)
    p._expression = '^' + p._expression + '$'
    return p.search(full_url_pattern)


def select_path(paths, path):
    max_path_size = 0
    result = None
    for path_pattern in paths:
        if path_pattern == path:
            return path_pattern

        if search(path_pattern, path) and len(path_pattern) > max_path_size:
            result = path_pattern
            max_path_size = len(path_pattern)

    return result


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_str(strings_only=True).
    """
    return isinstance(obj, _PROTECTED_TYPES)


def force_bytes(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_bytes, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first for performance reasons.
    if isinstance(s, bytes):
        if encoding == 'utf-8':
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)
    if strings_only and is_protected_type(s):
        return s
    if isinstance(s, memoryview):
        return bytes(s)
    return str(s).encode(encoding, errors)
