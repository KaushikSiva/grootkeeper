from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

try:
    from .config import settings
    from .schemas import GrootAction, GrootObservation
    from .system_checks import LIKELY_GROOT_MODULES
except ImportError:
    from config import settings
    from schemas import GrootAction, GrootObservation
    from system_checks import LIKELY_GROOT_MODULES


REAL_GROOT_API_MESSAGE = (
    "Real GR00T policy API not wired. Open backend/groot_client.py and map "
    "NVIDIA Isaac-GR00T inference API here."
)


def smoke_mode_enabled() -> bool:
    return os.getenv("GROOT_SMOKE_ONLY", "0") == "1"


def groot_available() -> tuple[bool, str]:
    if settings.model_backend != "groot":
        return False, "MODEL_BACKEND must be groot for the real L3 path."

    repo_dir = Path(settings.groot_repo_dir).expanduser()
    if not settings.groot_repo_dir or not repo_dir.exists():
        return False, f"GROOT_REPO_DIR is missing or invalid: {repo_dir}"

    if smoke_mode_enabled():
        return True, "GROOT_SMOKE_ONLY=1 diagnostic mode enabled."

    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

    import_errors: list[str] = []
    for module_name in LIKELY_GROOT_MODULES:
        try:
            importlib.import_module(module_name)
            return True, f"Imported GR00T module candidate: {module_name}"
        except Exception as exc:
            import_errors.append(f"{module_name}: {exc}")

    return False, " ; ".join(import_errors) or "No GR00T modules could be imported."


def load_groot_policy():
    if settings.model_backend != "groot":
        raise RuntimeError(
            "MODEL_BACKEND must be groot for real L3 execution. Set MODEL_BACKEND=groot."
        )

    if smoke_mode_enabled():
        return {"mode": "smoke_only", "checkpoint": settings.groot_checkpoint}

    repo_dir = Path(settings.groot_repo_dir).expanduser()
    if not settings.groot_repo_dir or not repo_dir.exists():
        raise RuntimeError(
            f"GROOT_REPO_DIR does not exist: {repo_dir}. "
            "Clone Isaac-GR00T and follow the official install instructions first."
        )

    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

    imported_module = None
    for module_name in LIKELY_GROOT_MODULES:
        try:
            imported_module = importlib.import_module(module_name)
            break
        except Exception:
            continue

    if imported_module is None:
        raise RuntimeError(
            "Unable to import NVIDIA Isaac-GR00T modules from GROOT_REPO_DIR. "
            "Check the repo clone, Python environment, and official install instructions."
        )

    # TODO: Add GROOT_REPO_DIR subpackages required by the exact NVIDIA layout.
    # TODO: Import the real GR00T policy class or inference entrypoint from imported_module.
    # TODO: Load the checkpoint from settings.groot_checkpoint with the official API.
    # TODO: Return the instantiated policy object for reuse across requests.
    raise RuntimeError(REAL_GROOT_API_MESSAGE)


def run_groot_inference(observation: GrootObservation) -> list[GrootAction]:
    if smoke_mode_enabled():
        return [
            GrootAction(
                primitive="navigate",
                target="plastic_bottle",
                destination="dustbin",
                raw_model_output={"mode": "smoke_only", "step": 1},
                confidence=0.55,
            ),
            GrootAction(
                primitive="pick",
                target="plastic_bottle",
                raw_model_output={"mode": "smoke_only", "step": 2},
                confidence=0.6,
            ),
            GrootAction(
                primitive="place",
                target="plastic_bottle",
                destination="dustbin",
                raw_model_output={"mode": "smoke_only", "step": 3},
                confidence=0.6,
            ),
        ]

    policy = load_groot_policy()

    # TODO: Convert GrootObservation into the exact GR00T observation structure expected by NVIDIA.
    # TODO: Call the real inference API on the loaded policy with the converted observation.
    # TODO: Convert the returned action chunk, tokens, or embeddings into GrootAction records.
    # TODO: Preserve the raw model output for debugging and later Isaac controller mapping.
    _ = policy
    raise RuntimeError(REAL_GROOT_API_MESSAGE)
