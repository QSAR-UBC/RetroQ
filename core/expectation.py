from dataclasses import dataclass

@dataclass
class Expectation:
    """Describe the expected behavior of a compiler pass.

    Fields:
        gate_count: int - Expected relationship between the original and transformed gate counts: decrease, increase, or unchanged.

    Raises:
        ValueError: If gate_count is not a supported relationship.
    """

    gate_count: str = "decrease"

    def __post_init__(self) -> None:
        valid = {"decrease", "increase", "unchanged"}
        if self.gate_count not in valid:
            raise ValueError(
                f"Expectation.gate_count must be one of {sorted(valid)}, got {self.gate_count!r}"
            )
