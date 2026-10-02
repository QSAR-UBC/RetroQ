from dataclasses import dataclass
from typing import Any

@dataclass
class SemanticAndPropertyResult:
    """Holds semantic and property evaluation results for a run.

    Fields:
        gate_count: int - number of gates after the pass
        expectation_value: Any - numeric or structured value representing expectation measurement
    """

    details: str
    gate_count: int
    expectation_value: float