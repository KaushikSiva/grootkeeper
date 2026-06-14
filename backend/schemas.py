from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SceneObject(BaseModel):
    name: str
    object_type: str
    position: list[float]
    orientation: list[float] | None = None
    confidence: float = 1.0


class SceneState(BaseModel):
    source: str
    objects: list[SceneObject]


class TaskRequest(BaseModel):
    command: str


class GrootObservation(BaseModel):
    command: str
    scene: SceneState
    image_path: str | None = None
    proprioception: dict[str, Any] = Field(default_factory=dict)


class GrootAction(BaseModel):
    primitive: str
    target: str | None = None
    destination: str | None = None
    action_vector: list[float] | None = None
    raw_model_output: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None


class GrootPlan(BaseModel):
    command: str
    observation: GrootObservation
    actions: list[GrootAction]
    model_backend: str
    checkpoint: str
    status: str


class ExecuteResult(BaseModel):
    command: str
    plan: GrootPlan
    safety_status: str
    ros2_publish_status: str
    isaac_execution_status: str
    logs: list[dict[str, Any]]


class SystemStatus(BaseModel):
    gpu_ok: bool
    cuda_ok: bool
    groot_repo_ok: bool
    groot_import_ok: bool
    ros2_ok: bool
    isaac_sim_configured: bool
    notes: list[str]
