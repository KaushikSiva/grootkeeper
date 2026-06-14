from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from .config import settings
    from .schemas import SystemStatus
except ImportError:
    from config import settings
    from schemas import SystemStatus


LIKELY_GROOT_MODULES = (
    "gr00t",
    "gr00t.deploy",
    "gr00t.model",
    "isaac_gr00t",
)


def _run_command(command: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, f"Command not found: {command[0]}"
    except Exception as exc:
        return False, f"Command failed: {' '.join(command)} :: {exc}"

    output = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode == 0:
        return True, output
    return False, output or f"Command returned {completed.returncode}"


def check_gpu() -> tuple[bool, str]:
    return _run_command(["nvidia-smi"])


def check_cuda() -> tuple[bool, str]:
    if shutil.which("nvcc") is None:
        return False, "nvcc not found. CUDA toolkit may be missing or not on PATH."
    return _run_command(["nvcc", "--version"])


def check_groot_repo() -> tuple[bool, str]:
    repo_dir = Path(settings.groot_repo_dir).expanduser()
    if not settings.groot_repo_dir:
        return False, "GROOT_REPO_DIR is not set."
    if not repo_dir.exists():
        return False, f"GROOT_REPO_DIR does not exist: {repo_dir}"
    return True, f"GROOT_REPO_DIR exists: {repo_dir}"


def check_groot_import() -> tuple[bool, str]:
    repo_ok, repo_note = check_groot_repo()
    if not repo_ok:
        return False, repo_note

    repo_dir = str(Path(settings.groot_repo_dir).expanduser())
    if repo_dir not in sys.path:
        sys.path.insert(0, repo_dir)

    import_errors: list[str] = []
    for module_name in LIKELY_GROOT_MODULES:
        try:
            importlib.import_module(module_name)
            return True, f"Imported GR00T module candidate: {module_name}"
        except Exception as exc:
            import_errors.append(f"{module_name}: {exc}")

    joined = "; ".join(import_errors)
    return False, f"Unable to import likely GR00T modules. {joined}"


def check_ros2() -> tuple[bool, str]:
    return _run_command(["ros2", "--help"])


def check_isaac_sim_config() -> tuple[bool, str]:
    if not settings.isaac_sim_python:
        return False, "ISAAC_SIM_PYTHON is not set."

    isaac_python = Path(settings.isaac_sim_python).expanduser()
    if isaac_python.exists():
        return True, f"ISAAC_SIM_PYTHON exists: {isaac_python}"
    return False, f"ISAAC_SIM_PYTHON does not exist: {isaac_python}"


def get_system_status() -> SystemStatus:
    gpu_ok, gpu_note = check_gpu()
    cuda_ok, cuda_note = check_cuda()
    groot_repo_ok, groot_repo_note = check_groot_repo()
    groot_import_ok, groot_import_note = check_groot_import()
    ros2_ok, ros2_note = check_ros2()
    isaac_ok, isaac_note = check_isaac_sim_config()

    return SystemStatus(
        gpu_ok=gpu_ok,
        cuda_ok=cuda_ok,
        groot_repo_ok=groot_repo_ok,
        groot_import_ok=groot_import_ok,
        ros2_ok=ros2_ok,
        isaac_sim_configured=isaac_ok,
        notes=[
            gpu_note,
            cuda_note,
            groot_repo_note,
            groot_import_note,
            ros2_note,
            isaac_note,
        ],
    )
