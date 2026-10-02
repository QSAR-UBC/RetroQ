import pennylane as qml
import numpy as np
from core.semantic_and_property_result import SemanticAndPropertyResult
from typing import Any, Dict, List

def get_circuit_details(circuit, details):
    """Execute a PennyLane circuit and return a summary result.

    Args:
        circuit: A callable qnode (no-arg) that builds and executes a circuit
        details: A short string describing this circuit (used in the result).

    Returns:
        SemanticAndPropertyResult: contains details, gate_count, and expectation_value.
    """
    exp_val = circuit()
    tape = qml.workflow.construct_tape(circuit)()
    filtered_ops = [op for op in tape.operations if not isinstance(op, qml.GlobalPhase)]
    num_gates = len(filtered_ops)

    return SemanticAndPropertyResult(details, num_gates, exp_val)

def run_pennylane_stage_1(target_function, compiler_pass, compiler_pass_kwargs):
    """Run stage-1 PennyLane experiments comparing adjoint placement.

    This builds two circuits:
      - circuit_adjoint_outside: applies  target_function, then the adjoint of
        compiler_pass(target_function).
      - circuit_adjoint_inside: applies target_function, then compiler_pass
        applied to the adjoint of target_function.

    Args:
        target_function: Callable that builds the target circuit (no-arg).
        compiler_pass: Callable that accepts a function and kwargs and returns
            a transformed function (the compiler pass).
        compiler_pass_kwargs: Dict of keyword arguments passed to `compiler_pass`.

    Returns:
        tuple: Two SemanticAndPropertyResult objects for the two circuit variants.
    """
    with qml.queuing.AnnotatedQueue() as q:
        target_function()

    active_wires = sorted(list(qml.tape.QuantumScript(q.queue).wires))

    dev = qml.device("default.qubit")

    @qml.qnode(dev)
    def circuit_adjoint_outside():
        """Evaluate the target followed by the transformed adjoint."""
        target_function()
        qml.adjoint(compiler_pass(target_function, **compiler_pass_kwargs))()
        return [qml.expval(qml.Z(wire)) for wire in active_wires]

    dev = qml.device("default.qubit")

    @qml.qnode(dev)
    def circuit_adjoint_inside():
        """Evaluate the target followed by the adjoint of the transformed target."""
        target_function()
        compiler_pass(qml.adjoint(target_function), **compiler_pass_kwargs)()
        return [qml.expval(qml.Z(wire)) for wire in active_wires]

    return get_circuit_details(
        circuit_adjoint_inside, "compiler_pass(adjoint(func))"
    ), get_circuit_details(circuit_adjoint_outside, "adjoint(compiler_pass(func))")

def run_pennylane_stage_2(target_function, compiler_pass, compiler_pass_kwargs):
    """Run stage-2 PennyLane controlled-adjoint experiments.

    Constructs three controlled circuits using a dedicated  control  wire to
    compare different placements of adjoint  and  compiler_pass under control.

    Args:
        target_function: Callable that builds the target circuit (no-arg).
        compiler_pass: Callable that accepts a function and kwargs and returns
            a transformed function (the compiler pass).
        compiler_pass_kwargs: Dict of keyword arguments passed to `compiler_pass`.

    Returns:
        tuple: Three SemanticAndPropertyResult objects corresponding to the
            constructed controlled circuits.
    """

    with qml.queuing.AnnotatedQueue() as q:
        target_function()

    active_wires = sorted(list(qml.tape.QuantumScript(q.queue).wires))
    dev1 = qml.device("default.qubit", wires=["control"] + active_wires)

    @qml.qnode(dev1)
    def circuit_1():
        """Evaluate the transformed adjoint outside the controlled operation."""
        qml.H("control")
        qml.ctrl(target_function, control="control")()
        qml.adjoint(
            qml.ctrl(compiler_pass(target_function, **compiler_pass_kwargs), control="control")
        )()
        qml.H("control")
        return qml.expval(qml.PauliZ("control"))

    dev2 = qml.device("default.qubit", wires=["control"] + active_wires)

    @qml.qnode(dev2)
    def circuit_2():
        """Evaluate the adjoint of the controlled transformed operation."""
        qml.H("control")
        qml.ctrl(target_function, control="control")()
        qml.ctrl(
            qml.adjoint(compiler_pass(target_function, **compiler_pass_kwargs)), control="control"
        )()
        qml.H("control")
        return qml.expval(qml.PauliZ("control"))

    dev3 = qml.device("default.qubit", wires=["control"] + active_wires)

    @qml.qnode(dev3)
    def circuit_3():
        """Evaluate the controlled operation built from an adjoint target."""
        qml.H("control")
        qml.ctrl(target_function, control="control")()
        qml.ctrl(
            compiler_pass(qml.adjoint(target_function), **compiler_pass_kwargs), control="control"
        )()
        qml.H("control")
        return qml.expval(qml.PauliZ("control"))

    return (
        get_circuit_details(circuit_3, "control(compiler_pass(adjoint(func))"),
        get_circuit_details(circuit_2, "control(adjoint(compiler_pass(func))"),
        get_circuit_details(circuit_1, "adjoint(control(adjoint(compiler_pass(func))"),
    )

def get_pennylane_stage_1_baseline_metrics(target_function):
    """Generate baseline metrics for stage 1.

    Runs the target circuit followed by its adjoint and returns a summary of
    gate count and expectation values that serve as the stage-1 baseline.

    Args:
        target_function: Callable that builds the target circuit (no-arg).

    Returns:
        SemanticAndPropertyResult: Baseline metrics for stage 1.
    """
    with qml.queuing.AnnotatedQueue() as q:
        target_function()

    active_wires = sorted(list(qml.tape.QuantumScript(q.queue).wires))

    dev = qml.device("default.qubit")

    @qml.qnode(dev)
    def circuit():
        """Evaluate the target and its adjoint for the stage-1 baseline."""
        target_function()
        qml.adjoint(target_function)()
        return [qml.expval(qml.Z(wire)) for wire in active_wires]

    return get_circuit_details(circuit, "baseline")

def get_pennylane_stage_2_baseline_metrics(target_function):
    """Generate baseline metrics for stage 2 (controlled-adjoint baseline).

    Builds a circuit that uses a dedicated control wire and the controlled
    version of the target circuit and its adjoint, returning a summary used
    as the stage-2 baseline.

    Args:
        target_function: Callable that builds the target circuit (no-arg).

    Returns:
        SemanticAndPropertyResult: Baseline metrics for stage 2.
    """
    with qml.queuing.AnnotatedQueue() as q:
        target_function()

    active_wires = sorted(list(qml.tape.QuantumScript(q.queue).wires))
    dev = qml.device("default.qubit", wires=["control"] + active_wires)

    @qml.qnode(dev)
    def circuit():
        """Evaluate the controlled target and its adjoint for the baseline."""
        qml.H(0)
        qml.ctrl(target_function, control="control")()
        qml.adjoint(qml.ctrl(target_function, control="control"))()
        qml.H(0)
        return qml.expval(qml.PauliZ("control"))

    return get_circuit_details(circuit, "baseline")

def _extract_metrics(obj):
    """Normalise different metric object shapes to a standard tuple.

    Args:
        obj: Object exposing ``gate_count`` and ``expectation_value`` attributes,
            such as ``SemanticAndPropertyResult``.

    Returns:
        tuple: ``(gate_count, expectation_value, details)`` where ``details`` is
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
    """Compare extracted metrics against a baseline according to expectations.

    Args:
        actual_obj: Result object containing metrics from a transformed circuit.
        baseline_obj: Result object containing baseline metrics.
        expectation_gate_value: Expected gate-count relationship. Supported
            values are ``"unchanged"``, ``"decrease"``, and ``"increase"``.

    Returns:
        None: If gate count and expectation value satisfy the expectation.
        dict: Difference details when either comparison does not satisfy it.
    """
    baseline_gate, baseline_exp, _ = _extract_metrics(baseline_obj)
    actual_gate, actual_exp, detail = _extract_metrics(actual_obj)

    if expectation_gate_value == "unchanged":
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

def run_pennylane_retroq(target_function, compiler_pass, compiler_pass_kwargs, expectation):
    """Run the full retroQ comparison flow for a PennyLane target.

    This function computes stage-1 and stage-2 baseline metrics, runs the
    corresponding actual circuits using compiler_pass, and collects any
    differences vs. the baselines according to the provided `expectation`.

    Args:
        target_function: Callable that builds the target circuit without
            arguments.
        compiler_pass: Callable that returns a transformed function when applied
            to a target function.
        compiler_pass_kwargs: Keyword arguments passed to ``compiler_pass``.
        expectation: Object exposing ``gate_count`` describing expected gate
            behavior.

    Returns:
        dict: Mapping with ``stage_1_differences`` and
        ``stage_2_differences`` lists. Each list contains difference
        dictionaries and is empty when no differences are found.
    """
    stage_1_baseline_metrics = get_pennylane_stage_1_baseline_metrics(target_function)
    stage_2_baseline_metrics = get_pennylane_stage_2_baseline_metrics(target_function)
    stage_1_actual_metrics = run_pennylane_stage_1(
        target_function, compiler_pass, compiler_pass_kwargs
    )
    stage_2_actual_metrics = run_pennylane_stage_2(
        target_function, compiler_pass, compiler_pass_kwargs
    )

    expectation_gate = getattr(expectation, "gate_count")

    stage_1_diffs: List[Dict[str, Any]] = []
    stage_2_diffs: List[Dict[str, Any]] = []

    baseline = stage_1_baseline_metrics
    for actual in stage_1_actual_metrics:
        diff = _compare_metrics_to_baseline(actual, baseline, expectation_gate)
        if diff:
            stage_1_diffs.append(diff)

    for actual in stage_2_actual_metrics:
        diff = _compare_metrics_to_baseline(actual, stage_2_baseline_metrics, expectation_gate)
        if diff:
            stage_2_diffs.append(diff)

    return {
        "stage_1_differences": stage_1_diffs,
        "stage_2_differences": stage_2_diffs,
    }
