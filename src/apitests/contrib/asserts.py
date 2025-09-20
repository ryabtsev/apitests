from contextlib import contextmanager

from .. import points  # noqa: TID252

__all__ = (
    'CustomAssertsCaseMixin',
)


class CustomAssertsCaseMixin:
    @contextmanager
    def context_common(self, workflow):
        with super().context_common(workflow):  # type: ignore[misc]
            yield

        if self.generator_mode:  # type: ignore[attr-defined]
            if self.asserts:  # type: ignore[attr-defined]
                self.append_asserts(workflow)  # type: ignore[attr-defined]
        else:
            for point in workflow.points:
                if point.role == points.Role.ASSERT:
                    assert_method = point.path
                    assert_method(workflow)

            if not self.is_telemetry_mode():  # type: ignore[attr-defined]
                self.assert_uncalled_points(workflow)

    def assert_uncalled_points(self, workflow):
        points_uncalled = workflow.get_external_calls(called=False)
        points_uncalled = [point.raw for point in points_uncalled]
        self.assertFalse(  # type: ignore[attr-defined]
            bool(points_uncalled),
            'There are uncalled points: %s' % points_uncalled
        )
