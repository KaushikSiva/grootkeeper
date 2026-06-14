from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

try:
    from .config import settings
    from .groot_policy_client import PolicyClient
    from .schemas import GrootAction, GrootObservation, SceneObject
except ImportError:
    from config import settings
    from groot_policy_client import PolicyClient
    from schemas import GrootAction, GrootObservation, SceneObject


DEFAULT_IMAGE_SIZE = 224
DEFAULT_STATE_DIMS = {
    "base_height_command": 1,
    "eef_9d": 9,
    "gripper": 1,
    "gripper_position": 1,
    "joint_position": 14,
    "left_arm": 7,
    "left_hand": 12,
    "left_leg": 6,
    "navigate_command": 3,
    "projected_gravity": 3,
    "right_arm": 7,
    "right_hand": 12,
    "right_leg": 6,
    "single_arm": 5,
    "waist": 3,
    "x": 1,
    "y": 1,
    "z": 1,
    "roll": 1,
    "pitch": 1,
    "yaw": 1,
    "rx": 1,
    "ry": 1,
    "rz": 1,
    "rw": 1,
}


def smoke_mode_enabled() -> bool:
    return os.getenv("GROOT_SMOKE_ONLY", "0") == "1"


def _policy_client() -> PolicyClient:
    return PolicyClient(
        host=settings.groot_server_host,
        port=settings.groot_server_port,
        timeout_ms=settings.groot_server_timeout_ms,
        api_token=settings.groot_server_api_token or None,
    )


@lru_cache(maxsize=1)
def _get_modality_config() -> dict[str, dict[str, Any]]:
    client = _policy_client()
    try:
        return client.get_modality_config()
    finally:
        client.close()


def _normalize_modality_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {"delta_indices": [0], "modality_keys": []}
    delta_indices = config.get("delta_indices") or [0]
    modality_keys = config.get("modality_keys") or []
    return {
        "delta_indices": list(delta_indices),
        "modality_keys": [str(key) for key in modality_keys],
    }


def _scene_image(observation: GrootObservation, image_size: int = DEFAULT_IMAGE_SIZE) -> np.ndarray:
    if observation.image_path:
        image_path = Path(observation.image_path).expanduser()
        if image_path.exists():
            with Image.open(image_path) as handle:
                image = handle.convert("RGB").resize((image_size, image_size))
                return np.asarray(image, dtype=np.uint8)

    if settings.groot_observation_image_path:
        image_path = Path(settings.groot_observation_image_path).expanduser()
        if image_path.exists():
            with Image.open(image_path) as handle:
                image = handle.convert("RGB").resize((image_size, image_size))
                return np.asarray(image, dtype=np.uint8)

    canvas = Image.new("RGB", (image_size, image_size), (12, 18, 28))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, image_size * 0.6, image_size, image_size), fill=(26, 41, 60))

    objects = observation.scene.objects or []
    xs = [obj.position[0] for obj in objects]
    ys = [obj.position[1] for obj in objects]
    min_x = min(xs, default=-1.0)
    max_x = max(xs, default=2.0)
    min_y = min(ys, default=-1.0)
    max_y = max(ys, default=2.0)
    span_x = max(max_x - min_x, 1e-3)
    span_y = max(max_y - min_y, 1e-3)

    def color_for(obj: SceneObject) -> tuple[int, int, int]:
        if obj.object_type == "trash":
            return (118, 228, 167)
        if obj.object_type == "container":
            return (247, 185, 85)
        if obj.object_type == "hazard":
            return (255, 107, 107)
        if obj.object_type == "robot":
            return (117, 180, 255)
        return (225, 232, 240)

    for obj in objects:
        x = int(((obj.position[0] - min_x) / span_x) * (image_size - 40) + 20)
        y = int(((obj.position[1] - min_y) / span_y) * (image_size - 40) + 20)
        radius = 12 if obj.object_type == "robot" else 8
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color_for(obj))

    return np.asarray(canvas, dtype=np.uint8)


def _guess_target(observation: GrootObservation) -> str | None:
    command = observation.command.lower()
    for obj in observation.scene.objects:
        if obj.object_type == "trash" and obj.name.lower() in command:
            return obj.name
    for obj in observation.scene.objects:
        if obj.object_type == "trash":
            return obj.name
    return None


def _guess_destination(observation: GrootObservation) -> str | None:
    command = observation.command.lower()
    for obj in observation.scene.objects:
        if obj.object_type == "container" and obj.name.lower() in command:
            return obj.name
    if any(token in command for token in ("bin", "dustbin", "container", "basket")):
        for obj in observation.scene.objects:
            if obj.object_type == "container":
                return obj.name
    return None


def _state_dim(key: str, value: Any | None) -> int:
    if value is not None:
        array = np.asarray(value, dtype=np.float32)
        if array.ndim == 0:
            return 1
        if array.ndim == 1:
            return int(array.shape[0])
        return int(array.shape[-1])
    return settings.groot_state_dim_overrides.get(key, DEFAULT_STATE_DIMS.get(key, 1))


def _expected_state_dim(key: str) -> int:
    return settings.groot_state_dim_overrides.get(key, DEFAULT_STATE_DIMS.get(key, 1))


def _split_joint_position_series(value: Any) -> tuple[np.ndarray, np.ndarray] | None:
    array = np.asarray(value, dtype=np.float32)
    total_dim = _expected_state_dim("left_arm") + _expected_state_dim("right_arm")
    if array.ndim == 0 or array.shape[-1] != total_dim:
        return None
    left_dim = _expected_state_dim("left_arm")
    return array[..., :left_dim], array[..., left_dim:]


def _combine_arm_series(left_arm: Any, right_arm: Any) -> np.ndarray | None:
    left = np.asarray(left_arm, dtype=np.float32)
    right = np.asarray(right_arm, dtype=np.float32)
    if left.ndim == 0 or right.ndim == 0:
        return None
    if left.shape[:-1] != right.shape[:-1]:
        return None
    if left.shape[-1] != _expected_state_dim("left_arm"):
        return None
    if right.shape[-1] != _expected_state_dim("right_arm"):
        return None
    return np.concatenate((left, right), axis=-1)


def _canonicalize_proprioception(
    proprioception: dict[str, Any],
    state_keys: list[str],
) -> dict[str, Any]:
    canonical = dict(proprioception)
    requested = set(state_keys)

    combined_source = (
        canonical.get("joint_position")
        if "joint_position" in canonical
        else canonical.get("joint_positions")
    )
    split_series = _split_joint_position_series(combined_source) if combined_source is not None else None
    if split_series is not None:
        left_arm, right_arm = split_series
        if "left_arm" in requested:
            canonical["left_arm"] = left_arm
        if "right_arm" in requested:
            canonical["right_arm"] = right_arm

    if "left_arm" in requested and "right_arm" in requested:
        if "left_arm" in canonical and _state_dim("left_arm", canonical["left_arm"]) == _expected_state_dim(
            "joint_position"
        ):
            split_left = _split_joint_position_series(canonical["left_arm"])
            if split_left is not None:
                canonical["left_arm"], canonical["right_arm"] = split_left
        elif "right_arm" in canonical and _state_dim("right_arm", canonical["right_arm"]) == _expected_state_dim(
            "joint_position"
        ):
            split_right = _split_joint_position_series(canonical["right_arm"])
            if split_right is not None:
                canonical["left_arm"], canonical["right_arm"] = split_right

    if "joint_position" in requested and "joint_position" not in canonical:
        combined = _combine_arm_series(canonical.get("left_arm"), canonical.get("right_arm"))
        if combined is not None:
            canonical["joint_position"] = combined

    return canonical


def _raise_state_dim_error(key: str, actual_dim: int, expected_dim: int) -> None:
    hint = ""
    if key in {"left_arm", "right_arm"} and actual_dim == _expected_state_dim("joint_position"):
        hint = (
            " Received a combined arm vector where a per-arm vector was expected;"
            " send `joint_position` or split the state into `left_arm` and `right_arm`."
        )
    raise ValueError(
        f"Invalid proprioception width for `{key}`: expected {expected_dim}, got {actual_dim}.{hint}"
    )


def _default_state_value(key: str, expected_dim: int) -> np.ndarray:
    if key == "eef_9d" and expected_dim == 9:
        return np.asarray([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0], dtype=np.float32)
    return np.zeros(expected_dim, dtype=np.float32)


def _normalize_state_series(value: Any | None, horizon: int, key: str) -> np.ndarray:
    expected_dim = _expected_state_dim(key)
    array = np.asarray(
        value if value is not None else _default_state_value(key, expected_dim),
        dtype=np.float32,
    )
    if array.ndim == 0:
        array = array.reshape(1)
    actual_dim = int(array.shape[-1]) if array.ndim > 0 else 1
    if actual_dim != expected_dim:
        _raise_state_dim_error(key, actual_dim, expected_dim)
    if array.ndim == 1:
        array = np.repeat(array[np.newaxis, :], horizon, axis=0)
    elif array.ndim == 2 and array.shape[0] != horizon:
        array = np.repeat(array.reshape(1, -1), horizon, axis=0)
    elif array.ndim > 2:
        array = array.reshape(horizon, -1) if array.shape[0] == horizon else np.repeat(
            array.reshape(1, -1),
            horizon,
            axis=0,
        )
    return array.astype(np.float32, copy=False)


def _build_policy_observation(
    observation: GrootObservation,
    modality_config: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    policy_observation: dict[str, Any] = {}

    video_cfg = _normalize_modality_config(modality_config.get("video"))
    state_cfg = _normalize_modality_config(modality_config.get("state"))
    language_cfg = _normalize_modality_config(modality_config.get("language"))

    base_image = _scene_image(observation)
    video_horizon = max(len(video_cfg["delta_indices"]), 1)
    state_horizon = max(len(state_cfg["delta_indices"]), 1)

    if video_cfg["modality_keys"]:
        policy_observation["video"] = {
            key: np.repeat(base_image[np.newaxis, np.newaxis, ...], video_horizon, axis=1)
            for key in video_cfg["modality_keys"]
        }

    if state_cfg["modality_keys"]:
        proprio = _canonicalize_proprioception(
            observation.proprioception or {},
            state_cfg["modality_keys"],
        )
        policy_observation["state"] = {
            key: _normalize_state_series(proprio.get(key), state_horizon, key)[np.newaxis, ...]
            for key in state_cfg["modality_keys"]
        }

    language_keys = language_cfg["modality_keys"] or ["annotation.human.task_description"]
    policy_observation["language"] = {key: [[observation.command]] for key in language_keys}
    return policy_observation


def _normalize_action_array(value: Any) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32)
    if array.ndim == 1:
        array = array[np.newaxis, np.newaxis, :]
    elif array.ndim == 2:
        array = array[np.newaxis, :, :]
    elif array.ndim != 3:
        raise RuntimeError(f"Unsupported action tensor shape: {array.shape}")
    return array


def _decode_groot_actions(
    action_chunk: dict[str, Any],
    info: dict[str, Any],
    observation: GrootObservation,
) -> list[GrootAction]:
    if not action_chunk:
        raise RuntimeError("GR00T policy returned an empty action payload.")

    normalized = {key: _normalize_action_array(value) for key, value in action_chunk.items()}
    horizon = max(array.shape[1] for array in normalized.values())
    target = _guess_target(observation)
    destination = _guess_destination(observation)
    confidence = info.get("confidence")

    actions: list[GrootAction] = []
    for step_idx in range(horizon):
        concatenated: list[float] = []
        raw_step: dict[str, Any] = {"policy_info": info, "per_key": {}}
        for key in sorted(normalized):
            current = normalized[key]
            row = current[0, min(step_idx, current.shape[1] - 1)]
            concatenated.extend(float(value) for value in row.tolist())
            raw_step["per_key"][key] = row.tolist()

        actions.append(
            GrootAction(
                primitive="policy_action",
                target=target,
                destination=destination,
                action_vector=concatenated,
                raw_model_output=raw_step,
                confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
            )
        )
    return actions


def get_groot_status() -> dict[str, Any]:
    available, note = groot_available()
    payload: dict[str, Any] = {
        "model_backend": settings.model_backend,
        "transport": "policy_server",
        "groot_available": available,
        "groot_note": note,
        "server_host": settings.groot_server_host,
        "server_port": settings.groot_server_port,
        "embodiment_tag": settings.groot_embodiment_tag,
        "checkpoint": settings.groot_checkpoint,
        "repo_dir": settings.groot_repo_dir,
    }
    if available:
        try:
            payload["modality_config"] = _get_modality_config()
        except Exception:
            payload["modality_config"] = {}
    return payload


def groot_available() -> tuple[bool, str]:
    if settings.model_backend != "groot":
        return False, "MODEL_BACKEND must be groot for the GR00T path."

    if smoke_mode_enabled():
        return True, "GROOT_SMOKE_ONLY=1 diagnostic mode enabled."

    client = _policy_client()
    try:
        if client.ping():
            return (
                True,
                f"GROOT policy server reachable at tcp://{settings.groot_server_host}:{settings.groot_server_port}",
            )
        return (
            False,
            f"GROOT policy server unavailable at tcp://{settings.groot_server_host}:{settings.groot_server_port}. "
            "Start scripts/08a_run_groot_policy_server.sh first.",
        )
    finally:
        client.close()


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

    modality_config = _get_modality_config()
    try:
        policy_observation = _build_policy_observation(observation, modality_config)
    except ValueError as exc:
        raise RuntimeError(f"Invalid GR00T observation payload: {exc}") from exc

    client = _policy_client()
    try:
        action_chunk, info = client.get_action(policy_observation)
    except TimeoutError as exc:
        raise RuntimeError(
            f"Timed out waiting for the GR00T policy server at "
            f"tcp://{settings.groot_server_host}:{settings.groot_server_port}. "
            "Make sure the server is running and the first checkpoint load has completed."
        ) from exc
    finally:
        client.close()

    return _decode_groot_actions(action_chunk, info, observation)
