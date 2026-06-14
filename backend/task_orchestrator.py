from __future__ import annotations

from dataclasses import dataclass

try:
    from .config import settings
    from .groot_client import groot_available, run_groot_inference, smoke_mode_enabled
    from .isaac_scene_client import get_scene_state_from_isaac_placeholder
    from .ros2_client import publish_groot_actions_to_ros
    from .safety import validate_before_execution
    from .schemas import ExecuteResult, GrootObservation, GrootPlan
except ImportError:
    from config import settings
    from groot_client import groot_available, run_groot_inference, smoke_mode_enabled
    from isaac_scene_client import get_scene_state_from_isaac_placeholder
    from ros2_client import publish_groot_actions_to_ros
    from safety import validate_before_execution
    from schemas import ExecuteResult, GrootObservation, GrootPlan


@dataclass
class OrchestratorError(Exception):
    message: str
    next_steps: list[str]

    def __str__(self) -> str:
        return self.message


def create_observation(command: str) -> GrootObservation:
    scene = get_scene_state_from_isaac_placeholder()
    return GrootObservation(command=command, scene=scene, proprioception={})


def plan_with_groot(command: str, require_real: bool = True) -> GrootPlan:
    available, note = groot_available()
    if not available and not smoke_mode_enabled():
        raise OrchestratorError(
            message=f"GR00T unavailable: {note}",
            next_steps=[
                "Run ./scripts/03_clone_or_check_groot.sh",
                "Run ./scripts/04_groot_smoke_test.sh",
                "Open backend/groot_client.py if imports succeed but inference is not mapped",
            ],
        )

    if require_real and smoke_mode_enabled():
        raise OrchestratorError(
            message="GROOT_SMOKE_ONLY=1 diagnostic mode is enabled. Unset it for real L3 planning.",
            next_steps=[
                "Unset GROOT_SMOKE_ONLY on the GB10 runtime shell.",
                "Restart the backend with MODEL_BACKEND=groot.",
                "Use POST /groot/smoke only for deterministic diagnostics.",
            ],
        )

    observation = create_observation(command)
    try:
        actions = run_groot_inference(observation)
    except RuntimeError as exc:
        raise OrchestratorError(
            message=str(exc),
            next_steps=[
                "Confirm GROOT_REPO_DIR and GROOT_CHECKPOINT in .env.",
                "Run python backend/groot_smoke_test.py.",
                "Open backend/groot_client.py and wire the official NVIDIA Isaac-GR00T inference API.",
            ],
        ) from exc

    status = "smoke_only" if smoke_mode_enabled() else "ok"
    return GrootPlan(
        command=command,
        observation=observation,
        actions=actions,
        model_backend=settings.model_backend,
        checkpoint=settings.groot_checkpoint,
        status=status,
    )


def execute_l3(command: str) -> ExecuteResult:
    plan = plan_with_groot(command=command, require_real=True)
    safety_status = validate_before_execution(plan)
    if safety_status != "approved":
        raise OrchestratorError(
            message=f"Safety blocked execution: {safety_status}",
            next_steps=[
                "Inspect the scene objects and object_type mapping from Isaac.",
                "Inspect the returned GR00T actions and destination names.",
                "Update the Isaac controller mapping only after the safety contract is correct.",
            ],
        )

    ros2_status = publish_groot_actions_to_ros(plan.actions)
    isaac_status = (
        "awaiting_isaac_execution_listener"
        if ros2_status.startswith("published:")
        else "not_started"
    )

    return ExecuteResult(
        command=command,
        plan=plan,
        safety_status=safety_status,
        ros2_publish_status=ros2_status,
        isaac_execution_status=isaac_status,
        logs=[
            {"stage": "scene", "source": plan.observation.scene.source},
            {"stage": "groot", "status": plan.status},
            {"stage": "ros2", "status": ros2_status},
        ],
    )
