from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized = os.path.expandvars(value.strip().strip('"').strip("'"))
        os.environ.setdefault(key.strip(), normalized)


_load_dotenv(ENV_FILE)


def _json_env(name: str, default: dict[str, int] | None = None) -> dict[str, int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default or {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must decode to a JSON object")
    return {str(key): int(value) for key, value in parsed.items()}


@dataclass(slots=True)
class Settings:
    model_backend: str = os.getenv("MODEL_BACKEND", "groot")
    groot_repo_dir: str = os.getenv("GROOT_REPO_DIR", "")
    groot_checkpoint: str = os.getenv("GROOT_CHECKPOINT", "")
    groot_embodiment_tag: str = os.getenv("GROOT_EMBODIMENT_TAG", "new_embodiment")
    groot_server_host: str = os.getenv("GROOT_SERVER_HOST", "127.0.0.1")
    groot_server_port: int = int(os.getenv("GROOT_SERVER_PORT", "5555"))
    groot_server_timeout_ms: int = int(os.getenv("GROOT_SERVER_TIMEOUT_MS", "30000"))
    groot_server_api_token: str = os.getenv("GROOT_SERVER_API_TOKEN", "")
    groot_server_device: str = os.getenv("GROOT_SERVER_DEVICE", "cuda")
    groot_modality_config_path: str = os.getenv("GROOT_MODALITY_CONFIG_PATH", "")
    groot_state_dim_overrides: dict[str, int] = field(
        default_factory=lambda: _json_env("GROOT_STATE_DIM_OVERRIDES_JSON")
    )
    groot_scene_topic: str = os.getenv("GROOT_SCENE_TOPIC", "/trashbot/scene_state")
    groot_scene_timeout_sec: float = float(os.getenv("GROOT_SCENE_TIMEOUT_SEC", "1.0"))
    groot_scene_state_path: str = os.getenv("GROOT_SCENE_STATE_PATH", "")
    groot_observation_image_path: str = os.getenv("GROOT_OBSERVATION_IMAGE_PATH", "")
    isaac_sim_python: str = os.getenv("ISAAC_SIM_PYTHON", "")
    g1_usd_path: str = os.getenv("G1_USD_PATH", "")
    g1_robot_prim: str = os.getenv("G1_ROBOT_PRIM", "/World/G1")
    g1_embodiment_mode: str = os.getenv(
        "G1_EMBODIMENT_MODE",
        "fixed_upper_body_pick_place",
    )
    ros_distro: str = os.getenv("ROS_DISTRO", "jazzy")
    ros_domain_id: str = os.getenv(
        "ROS_DOMAIN_ID",
        os.getenv("TRASHBOT_ROS_DOMAIN_ID", "42"),
    )
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    app_name: str = "Grootkeeper"
    default_command: str = "Pick up trash in the room and put it in the dustbin"


settings = Settings()

if settings.model_backend != "groot":
    print(
        "WARNING: MODEL_BACKEND is not 'groot'. "
        "This repo requires MODEL_BACKEND=groot for the real L3 path."
    )
