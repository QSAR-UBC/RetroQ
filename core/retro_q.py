import pennylane_files.pennylane_helpers as pennylane_helpers
import qiskit_files.qiskit_helpers as qiskit_helpers
from core.expectation import Expectation
from dataclasses import dataclass, field

from typing import Any, Callable, Dict, List, Optional

@dataclass
class RetroQ:
    """
    RetroQ is a framework for evaluating quantum compiler passes against a target quantum program.

    Fields:
        target_program: Callable[..., Any] - the quantum program to be evaluated
        compiler_pass: Any - the compiler pass to be evaluated
        expectation: Expectation - the expected behavior of the compiler pass
        compiler_pass_kwargs: Optional[Dict[str, Any]] - additional keyword arguments for the compiler pass
        framework: str - the quantum computing framework to use ("pennylane" or
        "qiskit")

    """

    target_program: Callable[..., Any]
    compiler_pass: Any
    expectation: Expectation
    compiler_pass_kwargs: Optional[Dict[str, Any]] = field(default_factory=dict)
    framework: str = "pennylane"

    def __post_init__(self):
        if not callable(self.target_program):
            raise TypeError("target_program must be a callable function")

        if self.framework not in {"qiskit", "pennylane"}:
            raise NotImplementedError(
                f"RetroQ currently supports only the 'PennyLane' and 'Qiskit' frameworks, not '{self.framework}'."
            )

    def run(self) -> Dict[str, Any]:
        """
        Run RetroQ.

        returns:
            Dict[str, Any]: A dictionary containing the results of the RetroQ run.
        """
        if self.framework == "pennylane":
            return pennylane_helpers.run_pennylane_retroq(
                self.target_program, self.compiler_pass, self.compiler_pass_kwargs, self.expectation
            )
        elif self.framework == "qiskit":
            return qiskit_helpers.run_qiskit_retroq(
                self.target_program, self.compiler_pass, self.expectation
            )
