from typing import Any, Dict, List
import numpy as np
from core.semantic_and_property_result import SemanticAndPropertyResult
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit.transpiler import PassManager

from qiskit import QuantumCircuit

def get_circuit_details(circuit, exp_val, details):
    """Create a metric result for a Qiskit circuit.

    Args:
        circuit: Qiskit quantum circuit whose instructions should be counted.
        exp_val: Expectation value computed for the circuit.
        details: Description identifying the circuit or comparison being measured.

    Returns:
        SemanticAndPropertyResult: Result containing the description, gate count,
        and expectation value.
    """
    num_gates = len(circuit)
    return SemanticAndPropertyResult(details, num_gates, exp_val)

def run_qiskit_stage_1(target_function, compiler_pass):
    """Run stage-1 Qiskit experiments comparing adjoint placement.

    Args:
        target_function: Callable that returns the target ``QuantumCircuit``.
        compiler_pass: Callable that returns a Qiskit transpiler pass.
        compiler_pass_kwargs: Keyword arguments reserved for configuring the
            compiler pass.

    Returns:
        tuple[SemanticAndPropertyResult, SemanticAndPropertyResult]: Results for
        applying the pass inside and outside the inverse operation, respectively.
    """

    sub_circ = target_function()
    num_qubits = sub_circ.num_qubits

    circ_adjoint_inside = QuantumCircuit(num_qubits)
    circ_adjoint_inside.compose(sub_circ, inplace=True)
    out = PassManager([compiler_pass()]).run(sub_circ.inverse())

    circ_adjoint_inside.compose(out, inplace=True)
    state = Statevector.from_instruction(circ_adjoint_inside)

    pauli_str = "Z" * num_qubits
    observable_circ_circ_adjoint_inside = SparsePauliOp(pauli_str)
    exp_val_circ_circ_adjoint_inside = state.expectation_value(observable_circ_circ_adjoint_inside)

    circ_adjoint_outside = QuantumCircuit(num_qubits)
    circ_adjoint_outside.compose(sub_circ, inplace=True)
    out = PassManager([compiler_pass()]).run(sub_circ)

    circ_adjoint_outside.compose(out.inverse(), inplace=True)
    state = Statevector.from_instruction(circ_adjoint_outside)

    pauli_str = "Z" * num_qubits
    observable_circ_circ_adjoint_outside = SparsePauliOp(pauli_str)
    exp_val_circ_circ_adjoint_outside = state.expectation_value(
        observable_circ_circ_adjoint_outside
    )
    return get_circuit_details(
        circ_adjoint_inside, exp_val_circ_circ_adjoint_inside, "compiler_pass(adjoint(func))"
    ), get_circuit_details(
        circ_adjoint_outside, exp_val_circ_circ_adjoint_outside, "adjoint(compiler_pass(func))"
    )

def append_controlled_circuit(main_circ, sub_circ, control_qubit=0):
    """
    Append a controlled version of sub_circ to main_circ,
    while keeping the individual gates visible in the drawing.
    """
    for instruction in sub_circ.data:
        gate = instruction.operation

        target_qubits = [control_qubit] + [
            sub_circ.find_bit(q).index + 1 for q in instruction.qubits
        ]

        controlled_gate = gate.control(1)

        main_circ.append(controlled_gate, target_qubits)

def run_qiskit_stage_2(target_function, compiler_pass):
    """Run stage-2 controlled-adjoint experiments for a Qiskit target.

    Args:
        target_function: Callable that returns the target ``QuantumCircuit``.
        compiler_pass: Callable that returns a Qiskit transpiler pass.

    Returns:
        tuple[SemanticAndPropertyResult, SemanticAndPropertyResult]: Results for three variations of controlled-adjoint placement.
    """

    sub_circ = target_function()
    num_qubits = sub_circ.num_qubits + 1

    variant_1 = QuantumCircuit(num_qubits)

    variant_1.h(0)
    append_controlled_circuit(variant_1, target_function())
    compiled_F = PassManager([compiler_pass()]).run(target_function())

    append_controlled_circuit(variant_1, compiled_F.inverse())
    variant_1.h(0)

    variant_2 = QuantumCircuit(num_qubits)
    variant_2.h(0)
    append_controlled_circuit(variant_2, target_function())
    compiled_F = PassManager([compiler_pass()]).run(target_function())

    append_controlled_circuit(variant_2, compiled_F.inverse())

    variant_2.h(0)

    variant_3 = QuantumCircuit(num_qubits)
    variant_3.h(0)
    append_controlled_circuit(variant_3, target_function())

    compiled_F = PassManager([compiler_pass()]).run(target_function())

    append_controlled_circuit(variant_3, compiled_F)

    variant_3.h(0)

    string = "Z" + "I" * (num_qubits - 1)
    observable = SparsePauliOp(string)

    v1_state = Statevector.from_instruction(variant_1)
    v1_exp_val = v1_state.expectation_value(observable)

    v2_state = Statevector.from_instruction(variant_2)
    v2_exp_val = v2_state.expectation_value(observable)

    v3_state = Statevector.from_instruction(variant_3)
    v3_exp_val = v3_state.expectation_value(observable)

    return (
        get_circuit_details(variant_1, v1_exp_val, "control(compiler_pass(adjoint(func)))"),
        get_circuit_details(variant_2, v2_exp_val, "control(adjoint(compiler_pass(func))))"),
        get_circuit_details(variant_3, v3_exp_val, "adjoint(control(compiler_pass(func))))"),
    )

def get_qiskit_stage_1_baseline_metrics(target_function):
    """Generate baseline metrics for stage 1 using Qiskit.

    Runs the target circuit followed by its inverse and returns a summary used
    as the stage-1 baseline.

    Args:
        target_function: Callable that returns the target ``QuantumCircuit``.

    Returns:
        SemanticAndPropertyResult: Baseline gate count and expectation value.
    """
    sub_circ = target_function()
    num_qubits = sub_circ.num_qubits
    circ = QuantumCircuit(num_qubits)
    circ.compose(sub_circ, inplace=True)
    circ.compose(sub_circ.inverse(), inplace=True)

    state = Statevector.from_instruction(circ)

    pauli_str = "Z" * num_qubits
    observable = SparsePauliOp(pauli_str)
    exp_val = state.expectation_value(observable)

    return get_circuit_details(circ, exp_val, "baseline")

def append_controlled_subcircuit(target_qc, source_qc, control_qubits, target_qubits_map):
    """
    Appends a source circuit's instructions into a target circuit as individually
    multi-controlled gates, avoiding both opaque 'blobs' and full decomposition.

    Args:
        target_qc: QuantumCircuit to append into (qc2)
        source_qc: QuantumCircuit containing the operations to control (qc1)
        control_qubits: List of integer qubit indices in target_qc used as controls
        target_qubits_map: Dict mapping source_qc qubit indices to target_qc qubit indices
    """
    num_controls = len(control_qubits)

    for instruction in source_qc.data:
        gate = instruction.operation
        controlled_gate = gate.control(num_controls)

        original_indices = [source_qc.find_bit(q).index for q in instruction.qubits]

        mapped_targets = [target_qubits_map[idx] for idx in original_indices]

        full_qubit_list = control_qubits + mapped_targets

        target_qc.append(controlled_gate, full_qubit_list)

    return target_qc

def get_qiskit_stage_2_baseline_metrics(target_function):
    """Generate baseline metrics for stage 2 using Qiskit.

    Args:
        target_function: Callable that returns the target ``QuantumCircuit``.

    Returns:
        None: Stage-2 baseline generation is not implemented for Qiskit yet.
    """
    F = target_function()

    num_qubits = F.num_qubits + 1

    circ = QuantumCircuit(num_qubits)
    circ.h(0)

    for instruction, qargs, cargs in F.data:
        controlled_gate = instruction.control(1)

        target_qubits = [0] + [q._index + 1 for q in qargs]

        circ.append(controlled_gate, target_qubits)

    F_inverse = F.inverse()

    for instruction, qargs, cargs in F_inverse.data:
        controlled_gate = instruction.control(1)

        target_qubits = [0] + [q._index + 1 for q in qargs]

        circ.append(controlled_gate, target_qubits)

    circ.h(0)

    state = Statevector.from_instruction(circ)
    pauli_str = "Z" + "I" * (num_qubits - 1)
    observable = SparsePauliOp(pauli_str)
    exp_val = state.expectation_value(observable)

    return get_circuit_details(circ, exp_val, "baseline")

def _extract_metrics(obj):
    """Extract comparable metric fields from a result object.

    Args:
        obj: Object exposing ``gate_count`` and ``expectation_value`` attributes.

    Returns:
        tuple: ``(gate_count, expectation_value, details)``; ``details`` is
        ``None`` when the input object does not define it.

    Raises:
        TypeError: If ``obj`` does not expose the required metric attributes.
    """
    if hasattr(obj, "gate_count") and hasattr(obj, "expectation_value"):
        return obj.gate_count, obj.expectation_value, getattr(obj, "details", None)
    raise TypeError("Unsupported metrics object type")


def _compare_metrics_to_baseline(
    actual_obj, baseline_obj, expectation_gate_value
) -> Dict[str, Any] | None:
    """Compare actual metrics with a baseline.

    Args:
        actual_obj: Result object containing metrics from a transformed circuit.
        baseline_obj: Result object containing baseline metrics.
        expectation_gate_value: Expected gate-count relationship. Supported
            values are ``"same"``, ``"unchanged"``, ``"decrease"``, and
            ``"increase"``.

    Returns:
        None: If gate count and expectation value satisfy the expectation.
        dict: Difference details when either comparison does not satisfy it.
    """
    baseline_gate, baseline_exp, _ = _extract_metrics(baseline_obj)
    actual_gate, actual_exp, detail = _extract_metrics(actual_obj)

    if expectation_gate_value in {"same", "unchanged"}:
        gate_ok = actual_gate == baseline_gate
    elif expectation_gate_value == "decrease":
        gate_ok = actual_gate < baseline_gate
    elif expectation_gate_value == "increase":
        gate_ok = actual_gate > baseline_gate
    else:
        gate_ok = False

    exp_ok = bool(np.all(np.isclose(actual_exp, baseline_exp)))

    if gate_ok and exp_ok:
        return None

    return {
        "detail": detail,
        "differences": {
            "gate_count": {"baseline": baseline_gate, "actual": actual_gate, "ok": gate_ok},
            "expectation_value": {"baseline": baseline_exp, "actual": actual_exp, "ok": exp_ok},
        },
    }

def run_qiskit_retroq(target_function, compiler_pass, expectation):
    """Run the full retroQ comparison flow for a Qiskit target.

    Mirrors ``run_pennylane_retroq`` but using Qiskit helpers. Stage-2 results
    remain empty until the Qiskit stage-2 helpers are implemented.

    Args:
        target_function: Callable that returns the target ``QuantumCircuit``.
        compiler_pass: Callable that returns a Qiskit transpiler pass.

        expectation: Object exposing ``gate_count`` with the expected gate-count
            relationship.

    Returns:
        dict: Mapping with ``stage_1_differences`` and
        ``stage_2_differences`` lists.
    """
    stage_1_baseline_metrics = get_qiskit_stage_1_baseline_metrics(target_function)
    stage_1_actual_metrics = run_qiskit_stage_1(target_function, compiler_pass)

    stage_2_baseline_metrics = get_qiskit_stage_2_baseline_metrics(target_function)
    stage_2_actual_metrics = run_qiskit_stage_2(target_function, compiler_pass)

    expectation_gate = getattr(expectation, "gate_count")

    stage_1_diffs: List[Dict[str, Any]] = []
    stage_2_diffs: List[Dict[str, Any]] = []

    baseline = stage_1_baseline_metrics
    for actual in stage_1_actual_metrics:
        diff = _compare_metrics_to_baseline(actual, baseline, expectation_gate)
        if diff:
            stage_1_diffs.append(diff)

    baseline = stage_2_baseline_metrics
    for actual in stage_2_actual_metrics:
        diff = _compare_metrics_to_baseline(actual, baseline, expectation_gate)
        if diff:
            stage_2_diffs.append(diff)

    return {
        "stage_1_differences": stage_1_diffs,
        "stage_2_differences": stage_2_diffs,
    }
