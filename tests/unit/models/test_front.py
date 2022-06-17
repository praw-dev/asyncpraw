"""Test asyncpraw.models.front."""
import pytest

from .. import UnitTest


class TestFront(UnitTest):
    def test_controversial_raises_value_error(self, reddit):
        with pytest.raises(ValueError):
            reddit.front.controversial("second")

    def test_top_raises_value_error(self, reddit):
        with pytest.raises(ValueError):
            reddit.front.top("second")
