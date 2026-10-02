import numpy as np
import pytest
from qiskit import QuantumCircuit

from core.semantic_and_property_result import SemanticAndPropertyResult
from pennylane_files.pennylane_helpers import _compare_metrics_to_baseline as compare_pennylane
from qiskit_files.qiskit_helpers import (
    _compare_metrics_to_baseline as compare_qiskit,
    get_circuit_details,
)

@pytest.mark.parametrize("compare", [compare_pennylane, compare_qiskit])
def test_metric_comparison_reports_gate_and_expectation_mismatches(compare):
    """
    Test that the metric comparison functions report mismatches in gate count and expectation value when the actual values
     do not match the baseline and expectation.
    """
    baseline = SemanticAndPropertyResult("baseline", 3, 0.5)
    actual = SemanticAndPropertyResult("actual", 4, 0.25)

    difference = compare(actual, baseline, "unchanged")

    assert difference["detail"] == "actual"
    assert difference["differences"]["gate_count"] == {
        "baseline": 3,
        "actual": 4,
        "ok": False,
    }
    assert difference["differences"]["expectation_value"]["ok"] == False


@pytest.mark.parametrize("compare", [compare_pennylane, compare_qiskit])
@pytest.mark.parametrize(
    "expectation_value",
    [np.float64(1.0), np.array([1.0])],
)
def test_metric_comparison_returns_builtin_bool_for_expectation(compare, expectation_value):
    baseline = SemanticAndPropertyResult("baseline", 3, expectation_value)
    actual = SemanticAndPropertyResult("actual", 4, expectation_value)

    difference = compare(actual, baseline, "unchanged")

    assert difference["differences"]["expectation_value"]["ok"] is True


def test_qiskit_get_circuit_details_counts_instructions():
    """
    Test that get_circuit_details correctly counts the number of instructions in a Qiskit circuit and returns the expected details."""
    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.x(0)

    result = get_circuit_details(circuit, np.float64(1.0), "example")

    assert result.details == "example"
    assert result.gate_count == 2
    assert result.expectation_value == np.float64(1.0)
