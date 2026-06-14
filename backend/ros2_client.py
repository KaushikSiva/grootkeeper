from __future__ import annotations

import json
import os
import shutil
import subprocess

try:
    from .config import settings
    from .schemas import GrootAction
except ImportError:
    from config import settings
    from schemas import GrootAction


def _ros_env() -> dict[str, str]:
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = str(settings.ros_domain_id)
    return env


def _publish_string_message(topic: str, payload: dict[str, object]) -> str:
    if shutil.which("ros2") is None:
        return "ROS 2 CLI unavailable. Install/source ROS 2 and verify `ros2 --help`."

    message = json.dumps(payload)
    command = [
        "ros2",
        "topic",
        "pub",
        "--once",
        topic,
        "std_msgs/msg/String",
        f"data: '{message}'",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=_ros_env(),
    )
    output = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode == 0:
        return f"published:{topic} :: {output or 'ok'}"
    return f"failed:{topic} :: {output or f'ros2 exited {completed.returncode}'}"


def publish_groot_actions_to_ros(actions: list[GrootAction]) -> str:
    payload = {
        "source": "grootkeeper_backend",
        "robot": "unitree_g1",
        "embodiment_mode": settings.g1_embodiment_mode,
        "checkpoint": settings.groot_checkpoint,
        "actions": [action.model_dump() for action in actions],
    }
    return _publish_string_message("/trashbot/groot_action", payload)


def publish_stop_to_ros() -> str:
    return _publish_string_message(
        "/trashbot/groot_action",
        {
            "source": "grootkeeper_backend",
            "type": "stop",
            "reason": "operator_requested_stop",
        },
    )
