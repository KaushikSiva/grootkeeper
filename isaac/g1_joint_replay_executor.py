from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


try:
    import omni.kit.app
    import omni.timeline
    import omni.usd
    try:
        from omni.isaac.core.articulations import Articulation
    except Exception:
        from isaacsim.core.prims import SingleArticulation as Articulation
    from pxr import Gf, UsdGeom
except Exception as exc:  # pragma: no cover - only importable inside Isaac Sim
    raise RuntimeError(
        "Could not import Isaac articulation APIs. Run this inside Isaac Sim Script Editor and "
        "enable the core Isaac Sim extension set first. Original error: "
        f"{exc!r}"
    ) from exc

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except Exception as exc:  # pragma: no cover - only importable inside Isaac Sim
    raise RuntimeError(
        "ROS 2 Python support is unavailable inside this Isaac Sim session."
    ) from exc


DEFAULT_G1_PRIM_PATH = os.getenv("G1_ROBOT_PRIM", "/World/G1")
DEFAULT_EXECUTION_MODE = os.getenv("G1_EMBODIMENT_MODE", "fixed_upper_body_pick_place")
DEFAULT_BOTTLE_PRIM_PATH = "/World/plastic_bottle"
DEFAULT_DUSTBIN_PRIM_PATH = "/World/dustbin"
DEFAULT_ARM_HINTS = (
    "left_shoulder",
    "left_elbow",
    "left_wrist",
    "left_arm",
    "shoulder_pitch",
    "shoulder_roll",
    "shoulder_yaw",
    "elbow",
    "wrist",
)


@dataclass
class ReplayFrame:
    joint_position: list[float]
    gripper_position: float
    raw_action: dict[str, Any]


def _load_arm_joint_override() -> list[str]:
    raw = os.getenv("G1_ARM_JOINTS_JSON", "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[g1_joint_replay_executor] Invalid G1_ARM_JOINTS_JSON: {exc}")
        return []
    if not isinstance(parsed, list):
        print("[g1_joint_replay_executor] G1_ARM_JOINTS_JSON must decode to a JSON list.")
        return []
    return [str(item) for item in parsed]


class GrootReplayNode(Node):
    def __init__(self, executor: "G1JointReplayExecutor") -> None:
        super().__init__("isaac_g1_joint_replay_executor")
        self._executor = executor
        self._subscription = self.create_subscription(
            String,
            "/trashbot/groot_action",
            self._on_action,
            10,
        )
        self._publisher = self.create_publisher(String, "/trashbot/execution_log", 10)

    def _on_action(self, msg: String) -> None:
        self.get_logger().info("Received /trashbot/groot_action payload.")
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().error(f"Invalid groot_action JSON: {exc}")
            return
        self._executor.load_payload(payload)

    def publish_log(self, payload: dict[str, Any]) -> None:
        message = String()
        message.data = json.dumps(payload)
        self._publisher.publish(message)


class G1JointReplayExecutor:
    def __init__(self) -> None:
        self.robot_prim_path = DEFAULT_G1_PRIM_PATH
        self.execution_mode = DEFAULT_EXECUTION_MODE
        self.node: GrootReplayNode | None = None
        self.articulation: Articulation | None = None
        self.arm_joint_names: list[str] = []
        self.arm_joint_indices: list[int] = []
        self.active_joint_count = 0
        self.frames: list[ReplayFrame] = []
        self.frame_index = 0
        self._app_subscription = None
        self._initialized = False
        self._last_logged_state = ""
        self.completed = False
        self.bottle_prim_path = DEFAULT_BOTTLE_PRIM_PATH
        self.dustbin_prim_path = DEFAULT_DUSTBIN_PRIM_PATH
        self.initial_bottle_position = Gf.Vec3d(0.72, 0.14, 0.75)
        self.dustbin_position = Gf.Vec3d(1.05, -0.42, 0.19)
        self.carry_height = 0.96

    def start(self) -> None:
        if not rclpy.ok():
            rclpy.init(args=None)
        self.node = GrootReplayNode(self)
        app = omni.kit.app.get_app()
        self._app_subscription = app.get_update_event_stream().create_subscription_to_pop(
            self._on_update,
            name="grootkeeper.g1_joint_replay_executor",
        )
        print("[g1_joint_replay_executor] Started. Listening on /trashbot/groot_action")
        print(f"[g1_joint_replay_executor] Robot prim path: {self.robot_prim_path}")
        print(
            "[g1_joint_replay_executor] If joint auto-detection is wrong, set "
            "G1_ARM_JOINTS_JSON to an explicit JSON list before launching Isaac Sim."
        )

    def stop(self) -> None:
        if self._app_subscription is not None:
            self._app_subscription.unsubscribe()
            self._app_subscription = None
        if self.node is not None:
            self.node.destroy_node()
            self.node = None
        self.frames = []
        self.frame_index = 0
        self._initialized = False
        self.completed = False
        print("[g1_joint_replay_executor] Stopped.")

    def load_payload(self, payload: dict[str, Any]) -> None:
        actions = payload.get("actions", [])
        frames: list[ReplayFrame] = []
        for action in actions:
            per_key = action.get("raw_model_output", {}).get("per_key", {})
            joint_position = per_key.get("joint_position") or []
            gripper_position = per_key.get("gripper_position") or [0.0]
            if not isinstance(joint_position, list) or len(joint_position) < 6:
                continue
            frames.append(
                ReplayFrame(
                    joint_position=[float(value) for value in joint_position],
                    gripper_position=float(gripper_position[0]) if gripper_position else 0.0,
                    raw_action=action,
                )
            )

        self.frames = frames
        self.frame_index = 0
        self.completed = False
        self._cache_scene_targets()

        summary = {
            "robot": "unitree_g1",
            "embodiment_mode": payload.get("embodiment_mode", self.execution_mode),
            "received_actions": len(actions),
            "replayable_joint_frames": len(self.frames),
            "mode": "isaac_joint_replay",
        }
        if self.node is not None:
            self.node.publish_log(summary)

        print(
            "[g1_joint_replay_executor] Loaded "
            f"{len(self.frames)} replay frames out of {len(actions)} actions."
        )
        if not self.frames:
            print(
                "[g1_joint_replay_executor] No replayable `joint_position` frames found. "
                "Expected 6- or 7-element per-step vectors."
            )

    def _on_update(self, _event: Any) -> None:
        if self.node is not None:
            rclpy.spin_once(self.node, timeout_sec=0.0)

        if not self._initialized:
            self._try_initialize_articulation()
            return

        if not self.frames or self.articulation is None:
            self._log_once("waiting", "[g1_joint_replay_executor] Waiting for replay frames...")
            return

        if self.completed:
            self._log_once("completed", "[g1_joint_replay_executor] Replay complete. Waiting for next payload.")
            return

        timeline = omni.timeline.get_timeline_interface()
        if hasattr(timeline, "is_playing") and not timeline.is_playing():
            self._log_once(
                "timeline",
                "[g1_joint_replay_executor] Isaac timeline is paused. Press Play in Isaac Sim.",
            )
            return

        if self.frame_index >= len(self.frames):
            self.completed = True
            self._place_bottle_in_bin()
            if self.node is not None:
                self.node.publish_log(
                    {
                        "robot": "unitree_g1",
                        "mode": "isaac_joint_replay",
                        "status": "complete",
                        "replayed_frames": len(self.frames),
                    }
                )
            return

        frame = self.frames[self.frame_index]
        self._apply_frame(frame)
        self._update_demo_object_motion()
        self.frame_index += 1

    def _try_initialize_articulation(self) -> None:
        try:
            articulation = Articulation(prim_path=self.robot_prim_path, name="g1_replay_robot")
            articulation.initialize()
            dof_names = list(articulation.dof_names)
        except Exception as exc:
            self._log_once(
                "init_failed",
                f"[g1_joint_replay_executor] Waiting for articulation at {self.robot_prim_path}: {exc}",
            )
            return

        self.articulation = articulation
        self.arm_joint_names, self.arm_joint_indices = self._resolve_arm_joint_indices(dof_names)
        if len(self.arm_joint_indices) not in {6, 7}:
            print("[g1_joint_replay_executor] Could not resolve a 6- or 7-joint arm mapping.")
            print(f"[g1_joint_replay_executor] Available DOFs: {dof_names}")
            print(
                "[g1_joint_replay_executor] Set G1_ARM_JOINTS_JSON in the Isaac Sim environment "
                "to the exact 6 or 7 joint names for the arm you want to drive."
            )
            return

        self.active_joint_count = len(self.arm_joint_indices)
        self._initialized = True
        print(f"[g1_joint_replay_executor] Articulation initialized at {self.robot_prim_path}")
        print(f"[g1_joint_replay_executor] Using arm joints: {self.arm_joint_names}")

    def _resolve_arm_joint_indices(self, dof_names: list[str]) -> tuple[list[str], list[int]]:
        override = _load_arm_joint_override()
        if override:
            indices = [dof_names.index(name) for name in override if name in dof_names]
            return override, indices

        lowered = [(index, name, name.lower()) for index, name in enumerate(dof_names)]
        matches = []
        for index, name, lowered_name in lowered:
            if any(hint in lowered_name for hint in DEFAULT_ARM_HINTS):
                matches.append((index, name))

        if len(matches) >= 7:
            chosen = matches[:7]
            return [name for _, name in chosen], [index for index, _ in chosen]

        if len(matches) >= 6:
            chosen = matches[:6]
            return [name for _, name in chosen], [index for index, _ in chosen]

        return [], []

    def _apply_frame(self, frame: ReplayFrame) -> None:
        if self.articulation is None or self.active_joint_count not in {6, 7}:
            return
        try:
            current_positions = list(self.articulation.get_joint_positions())
        except Exception as exc:
            self._log_once(
                "joint_read_failed",
                f"[g1_joint_replay_executor] Failed to read joint positions: {exc}",
            )
            return

        for offset, joint_index in enumerate(self.arm_joint_indices):
            current_positions[joint_index] = frame.joint_position[offset]

        try:
            self.articulation.set_joint_positions(current_positions)
        except Exception as exc:
            self._log_once(
                "joint_write_failed",
                f"[g1_joint_replay_executor] Failed to set joint positions: {exc}",
            )
            return

    def _cache_scene_targets(self) -> None:
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return
        bottle_prim = stage.GetPrimAtPath(self.bottle_prim_path)
        dustbin_prim = stage.GetPrimAtPath(self.dustbin_prim_path)
        self.initial_bottle_position = self._extract_translation(bottle_prim, self.initial_bottle_position)
        self.dustbin_position = self._extract_translation(dustbin_prim, self.dustbin_position)
        self._set_translation(bottle_prim, self.initial_bottle_position)

    def _extract_translation(self, prim, fallback: Gf.Vec3d) -> Gf.Vec3d:
        if prim is None or not prim.IsValid():
            return fallback
        xformable = UsdGeom.Xformable(prim)
        for op in xformable.GetOrderedXformOps():
            if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                value = op.Get()
                if value is not None:
                    return Gf.Vec3d(value[0], value[1], value[2])
        return fallback

    def _set_translation(self, prim, value: Gf.Vec3d) -> None:
        if prim is None or not prim.IsValid():
            return
        xformable = UsdGeom.Xformable(prim)
        translate_op = None
        for op in xformable.GetOrderedXformOps():
            if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                translate_op = op
                break
        if translate_op is None:
            translate_op = xformable.AddTranslateOp()
        translate_op.Set(value)

    def _update_demo_object_motion(self) -> None:
        if not self.frames:
            return
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return
        bottle_prim = stage.GetPrimAtPath(self.bottle_prim_path)
        if not bottle_prim or not bottle_prim.IsValid():
            return

        ratio = self.frame_index / max(len(self.frames) - 1, 1)
        if ratio < 0.55:
            bottle_position = self.initial_bottle_position
        elif ratio < 0.72:
            lift = (ratio - 0.55) / 0.17
            bottle_position = Gf.Vec3d(
                self.initial_bottle_position[0],
                self.initial_bottle_position[1],
                self.initial_bottle_position[2] + 0.18 * lift,
            )
        else:
            carry = min((ratio - 0.72) / 0.28, 1.0)
            source = Gf.Vec3d(
                self.initial_bottle_position[0],
                self.initial_bottle_position[1],
                self.carry_height,
            )
            target = Gf.Vec3d(
                self.dustbin_position[0],
                self.dustbin_position[1],
                self.dustbin_position[2] + 0.16,
            )
            bottle_position = Gf.Vec3d(
                source[0] + (target[0] - source[0]) * carry,
                source[1] + (target[1] - source[1]) * carry,
                source[2] + (target[2] - source[2]) * carry,
            )

        self._set_translation(bottle_prim, bottle_position)

    def _place_bottle_in_bin(self) -> None:
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return
        bottle_prim = stage.GetPrimAtPath(self.bottle_prim_path)
        if not bottle_prim or not bottle_prim.IsValid():
            return
        final_position = Gf.Vec3d(
            self.dustbin_position[0],
            self.dustbin_position[1],
            self.dustbin_position[2] + 0.1,
        )
        self._set_translation(bottle_prim, final_position)

    def _log_once(self, key: str, message: str) -> None:
        if self._last_logged_state == key:
            return
        self._last_logged_state = key
        print(message)


_EXECUTOR: G1JointReplayExecutor | None = None


def start() -> G1JointReplayExecutor:
    global _EXECUTOR
    if _EXECUTOR is not None:
        _EXECUTOR.stop()
    _EXECUTOR = G1JointReplayExecutor()
    _EXECUTOR.start()
    return _EXECUTOR


def stop() -> None:
    global _EXECUTOR
    if _EXECUTOR is not None:
        _EXECUTOR.stop()
        _EXECUTOR = None


start()
