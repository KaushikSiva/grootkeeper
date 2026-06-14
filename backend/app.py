from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .config import settings
    from .groot_client import groot_available, smoke_mode_enabled
    from .ros2_client import publish_stop_to_ros
    from .schemas import TaskRequest
    from .system_checks import get_system_status
    from .task_orchestrator import OrchestratorError, execute_l3, plan_with_groot
except ImportError:
    from config import settings
    from groot_client import groot_available, smoke_mode_enabled
    from ros2_client import publish_stop_to_ros
    from schemas import TaskRequest
    from system_checks import get_system_status
    from task_orchestrator import OrchestratorError, execute_l3, plan_with_groot


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _raise_orchestrator_http_error(exc: OrchestratorError) -> None:
    raise HTTPException(
        status_code=500,
        detail={
            "error": exc.message,
            "next_steps": exc.next_steps,
        },
    )


@app.get("/")
def root() -> dict[str, object]:
    return {
        "app": settings.app_name,
        "default_command": settings.default_command,
        "main_endpoint": "/execute_l3",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "app": settings.app_name}


@app.get("/status")
def status() -> dict[str, object]:
    available, note = groot_available()
    return {
        "app": settings.app_name,
        "model_backend": settings.model_backend,
        "groot_available": available,
        "groot_note": note,
        "smoke_mode": smoke_mode_enabled(),
    }


@app.get("/system/status")
def system_status() -> dict[str, object]:
    return get_system_status().model_dump()


@app.get("/groot/status")
def groot_status() -> dict[str, object]:
    available, note = groot_available()
    return {
        "available": available,
        "note": note,
        "checkpoint": settings.groot_checkpoint,
        "repo_dir": settings.groot_repo_dir,
    }


@app.post("/groot/smoke")
def groot_smoke(request: TaskRequest | None = None) -> dict[str, object]:
    if not smoke_mode_enabled():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "GROOT_SMOKE_ONLY=1 is required for the deterministic smoke path.",
                "next_steps": [
                    "Export GROOT_SMOKE_ONLY=1 on the GB10 shell.",
                    "Restart the backend.",
                    "Use /plan or /execute_l3 only after unsetting GROOT_SMOKE_ONLY.",
                ],
            },
        )

    command = request.command if request else settings.default_command
    try:
        return plan_with_groot(command=command, require_real=False).model_dump()
    except OrchestratorError as exc:
        _raise_orchestrator_http_error(exc)


@app.post("/plan")
def plan(request: TaskRequest) -> dict[str, object]:
    try:
        return plan_with_groot(command=request.command, require_real=True).model_dump()
    except OrchestratorError as exc:
        _raise_orchestrator_http_error(exc)


@app.post("/execute_l3")
def execute(request: TaskRequest) -> dict[str, object]:
    try:
        return execute_l3(command=request.command).model_dump()
    except OrchestratorError as exc:
        _raise_orchestrator_http_error(exc)


@app.post("/stop")
def stop() -> dict[str, object]:
    return {"status": publish_stop_to_ros()}
