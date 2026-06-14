from __future__ import annotations

import math

try:
    from .schemas import GrootPlan
except ImportError:
    from schemas import GrootPlan


def validate_before_execution(plan: GrootPlan) -> str:
    if plan.status != "ok":
        return f"blocked: plan status is {plan.status}"

    if not plan.actions:
        return "blocked: no actions produced by GR00T"

    object_types = {obj.name: obj.object_type for obj in plan.observation.scene.objects}

    for action in plan.actions:
        if action.target and object_types.get(action.target) == "hazard":
            return f"blocked: target {action.target} is a hazard"

        if action.primitive in {"drop", "release", "place"}:
            if not action.destination:
                return f"blocked: {action.primitive} requires a destination"
            if object_types.get(action.destination) != "container":
                return (
                    f"blocked: destination {action.destination} is not a container "
                    f"(found {object_types.get(action.destination)})"
                )

        if action.action_vector is not None:
            for value in action.action_vector:
                if not math.isfinite(value):
                    return f"blocked: action_vector contains non-finite value {value}"

    return "approved"
