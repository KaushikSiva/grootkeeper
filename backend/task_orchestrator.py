from __future__ import annotations

from dataclasses import dataclass

try:
    from .groot_client import groot_available, run_groot_inference, smoke_mode_enabled
    from .isaac_scene_client import get_scene_state
    from .ros2_client import publish_groot_actions_to_ros
    from .safety import validate_before_execution
    from .schemas import ExecuteResult, GrootObservation, GrootPlan, TaskRequest
except ImportError:
    from groot_client import groot_available, run_groot_inference, smoke_mode_enabled
    from isaac_scene_client import get_scene_state
    from ros2_client import publish_groot_actions_to_ros
    from safety import validate_before_execution
    from schemas import ExecuteResult, GrootObservation, GrootPlan, TaskRequest


@dataclass
class OrchestratorError(Exception):
    message: str
    next_steps: list[str]

    def __str__(self) -> str:
        return self.message


def create_observation(request: TaskRequest) -> GrootObservation:
    scene = request.scene_override or get_scene_state()
    return GrootObservation(
        command=request.command,
        scene=scene,
        image_path=request.image_path,
        proprioception=request.proprioception,
    )


def plan_with_groot(request: TaskRequest, require_real: bool = True) -> GrootPlan:
    available, note = groot_available()
    if not available and not smoke_mode_enabled():
        raise OrchestratorError(
            message=f"GR00T unavailable: {note}",
            next_steps=[
                "Start the GR00T policy server with ./scripts/08a_run_groot_policy_server.sh.",
                "Run ./scripts/09_test_backend_status.sh and confirm groot_server_ok=true.",
                "Verify GROOT_SERVER_HOST / GROOT_SERVER_PORT in .env match the server process.",
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

    observation = create_observation(request)
    try:
        actions = run_groot_inference(observation)
    except RuntimeError as exc:
        raise OrchestratorError(
            message=str(exc),
            next_steps=[
                "Confirm the GR00T policy server is running and reachable.",
                "Verify the server embodiment tag and modality config match the observations you send.",
                "Provide real image_path / proprioception inputs or publish live scene state before retrying.",
            ],
        ) from exc

    status = "smoke_only" if smoke_mode_enabled() else "ok"
    return GrootPlan(
        command=request.command,
        observation=observation,
        actions=actions,
        model_backend="groot",
        checkpoint="policy_server",
        status=status,
    )


def execute_l3(request: TaskRequest) -> ExecuteResult:
    plan = plan_with_groot(request=request, require_real=True)
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
        command=request.command,
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
