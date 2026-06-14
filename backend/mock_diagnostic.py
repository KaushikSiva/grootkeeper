from __future__ import annotations

from schemas import GrootAction


def mock_plan_for_debug(command: str) -> list[GrootAction]:
    # Diagnostic only. This is not the real L3 GR00T path.
    return [
        GrootAction(
            primitive="diagnostic_echo",
            target="plastic_bottle",
            destination="dustbin",
            raw_model_output={"mode": "mock_diagnostic", "command": command},
            confidence=0.25,
        )
    ]
