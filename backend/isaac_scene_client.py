from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess

try:
    from .config import settings
    from .schemas import SceneObject, SceneState
except ImportError:
    from config import settings
    from schemas import SceneObject, SceneState


def _placeholder_scene_state() -> SceneState:
    return SceneState(
        source="isaac_pose_placeholder",
        objects=[
            SceneObject(
                name="plastic_bottle",
                object_type="trash",
                position=[1.1, 0.4, 0.8],
                orientation=[0.0, 0.0, 0.0, 1.0],
            ),
            SceneObject(
                name="paper_wrapper",
                object_type="trash",
                position=[1.0, 0.1, 0.8],
                orientation=[0.0, 0.0, 0.0, 1.0],
            ),
            SceneObject(
                name="paper_cup",
                object_type="trash",
                position=[0.9, -0.15, 0.8],
                orientation=[0.0, 0.0, 0.0, 1.0],
            ),
            SceneObject(
                name="dustbin",
                object_type="container",
                position=[1.8, -0.4, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
            ),
            SceneObject(
                name="red_hazard_zone",
                object_type="hazard",
                position=[0.2, 1.3, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
            ),
            SceneObject(
                name="unitree_g1",
                object_type="robot",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
            ),
        ],
    )


def _scene_state_from_payload(payload: dict[str, object]) -> SceneState:
    return SceneState.model_validate(payload)


def _parse_ros_string_payload(output: str) -> dict[str, object]:
    if not output.strip():
        raise ValueError("Empty ROS scene_state output")

    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("data:"):
            raw = stripped.split("data:", 1)[1].strip()
            try:
                decoded = ast.literal_eval(raw)
            except Exception:
                decoded = raw.strip("\"'")
            return json.loads(decoded)

    return json.loads(output)


def _read_scene_state_from_file() -> SceneState | None:
    path = settings.groot_scene_state_path.strip()
    if not path:
        return None
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return _scene_state_from_payload(json.load(handle))


def _read_scene_state_from_ros() -> SceneState | None:
    if shutil.which("ros2") is None:
        return None

    command = [
        "ros2",
        "topic",
        "echo",
        "--once",
        settings.groot_scene_topic,
        "std_msgs/msg/String",
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=settings.groot_scene_timeout_sec,
            env={**os.environ, "ROS_DOMAIN_ID": str(settings.ros_domain_id)},
        )
    except subprocess.TimeoutExpired:
        return None

    if completed.returncode != 0:
        return None

    payload = _parse_ros_string_payload(completed.stdout or completed.stderr or "")
    scene = _scene_state_from_payload(payload)
    if scene.source == "isaac_pose_placeholder":
        scene.source = f"ros_topic:{settings.groot_scene_topic}"
    return scene


def get_scene_state() -> SceneState:
    for loader in (_read_scene_state_from_file, _read_scene_state_from_ros):
        scene = loader()
        if scene is not None:
            return scene
    return _placeholder_scene_state()


def publish_expected_scene_to_ros_placeholder() -> dict[str, object]:
    return {
        "status": "expect_live_scene_topic",
        "notes": [
            f"Publish {settings.groot_scene_topic} from Isaac Sim as JSON in std_msgs/String.",
            "Optionally write the same payload to GROOT_SCENE_STATE_PATH for file-based fallback.",
            "If neither live topic nor file is present, the backend falls back to its built-in scene skeleton.",
        ],
    }
