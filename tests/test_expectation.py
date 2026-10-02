import pytest

from core.expectation import Expectation

def test_expectation_rejects_unsupported_gate_count_relationship():
    """
    Test that Expectation raises a ValueError when an unsupported gate count relationship is specified."""
    with pytest.raises(ValueError, match="must be one of"):
        Expectation("same")
