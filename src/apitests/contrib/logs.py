from contextlib import contextmanager
from logging import Logger
from unittest.mock import patch

from .. import points  # noqa: TID252

__all__ = (
    'LogsTestCaseMixin',
)


def clean_msg(value):
    value = value.split('\n')[0]
    value = value.replace("'", '"')
    return value


class LogsTestCaseMixin:
    log_asserts_filter: list = []

    @contextmanager
    def context_common(self, workflow):
        with self.capture_logs():
            with super().context_common(workflow):  # type: ignore[misc]
                yield

    def use_capture(self, name):
        if self.log_asserts_filter:
            for prefix in self.log_asserts_filter:
                if name.startswith(prefix):
                    return True

        return True

    @contextmanager
    def capture_logs(self):
        logs_points = []

        test_case = self

        class ExtendedLogger(Logger):
            @classmethod
            def capture(cls, record):
                if not test_case.use_capture(record.name):
                    return

                point = points.PointLog(
                    record.levelname + ':' + record.name, clean_msg(record.getMessage()),
                    pattern=clean_msg(record.msg)
                )
                logs_points.append(point)
                if test_case.generator_mode:  # type: ignore[attr-defined]
                    # DISABLED: found a bug 
                    # test_case.extend_pipeline([point.raw])  # type: ignore[attr-defined]
                    return

            def isEnabledFor(self, level):
                return True

            def handle(self, record):
                self.capture(record)

        setattr(Logger, 'capture', ExtendedLogger.capture)
        setattr(Logger, 'handle', ExtendedLogger.handle)
        setattr(Logger, 'isEnabledFor', ExtendedLogger.isEnabledFor)

        yield

        # TODO: check logs against workflow
