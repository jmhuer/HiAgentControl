from __future__ import annotations


class DeliverableError(RuntimeError):
    """Raised when an opencode invoke returns without required on-disk artifacts."""

    def __init__(self, phase: str, message: str) -> None:
        self.phase = phase
        super().__init__(f"[{phase}] {message}")


# Backward-compatible alias
PhaseError = DeliverableError
