from __future__ import annotations

import os
from dataclasses import dataclass
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
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ENV_FILE)


@dataclass(slots=True)
class Settings:
    model_backend: str = os.getenv("MODEL_BACKEND", "groot")
    groot_repo_dir: str = os.getenv("GROOT_REPO_DIR", "")
    groot_checkpoint: str = os.getenv("GROOT_CHECKPOINT", "")
    isaac_sim_python: str = os.getenv("ISAAC_SIM_PYTHON", "")
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
