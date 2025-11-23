from textwrap import dedent
import pytest

def test_import() -> None:
    import amzn_waypoint_ai  # type: ignore # noqa: F401
