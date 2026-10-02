from unittest.mock import patch
import pytest

from core.expectation import Expectation
from core.retro_q import RetroQ

def target_program():
    return None

def test_retro_q_rejects_non_callable_target_program():
    """
    Test that RetroQ raises a TypeError when the target_program is not callable."""
    with pytest.raises(TypeError, match="target_program must be a callable"):
        RetroQ(None, object(), Expectation())

def test_retro_q_rejects_unsupported_framework():
    """
    Test that RetroQ raises a NotImplementedError when an unsupported framework is specified.
    """
    with pytest.raises(NotImplementedError, match="supports only"):
        RetroQ(target_program, object(), Expectation(), framework="not_a_framework")

@pytest.mark.parametrize("framework", ["pennylane", "qiskit"])
def test_retro_q_dispatches_to_selected_framework_helper(framework):
    """
    Test that RetroQ dispatches to the correct framework helper function based on the specified framework."""
    expected = {"stage_1_differences": [], "stage_2_differences": []}
    if framework == "pennylane":
        patch_target = "core.retro_q.pennylane_helpers.run_pennylane_retroq"
    else:
        patch_target = "core.retro_q.qiskit_helpers.run_qiskit_retroq"

    with patch(patch_target, return_value=expected) as helper:
        retro_q = RetroQ(
            target_program,
            object(),
            Expectation("unchanged"),
            compiler_pass_kwargs={"option": True},
            framework=framework,
        )

        assert retro_q.run() == expected
        if framework == "pennylane":
            helper.assert_called_once_with(
                target_program, retro_q.compiler_pass, {"option": True}, retro_q.expectation
            )
        else:
            helper.assert_called_once_with(
                target_program, retro_q.compiler_pass, retro_q.expectation
            )
