from __future__ import annotations

import json
import os
from pathlib import Path


DEFAULT_G1_PRIM_PATH = "/World/G1"
G1_ASSET_ENV_VARS = ("G1_USD_PATH", "UNITREE_G1_USD_PATH", "GROOTKEEPER_G1_USD")


def _publish_scene_state_if_ros2_available(scene_objects: list[dict[str, object]]) -> None:
    try:
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import String
    except Exception:
        print("ROS 2 Python libraries not available in this Isaac session. Skipping scene_state publish.")
        return

    class ScenePublisher(Node):
        def __init__(self) -> None:
            super().__init__("trashbot_scene_publisher")
            self.publisher = self.create_publisher(String, "/trashbot/scene_state", 10)

    rclpy.init(args=None)
    node = ScenePublisher()
    try:
        message = String()
        message.data = json.dumps(
            {
                "source": "isaac_sim_scene_script",
                "objects": scene_objects,
            }
        )
        node.publisher.publish(message)
        rclpy.spin_once(node, timeout_sec=0.2)
        print("Published /trashbot/scene_state from Isaac scene skeleton.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _resolve_g1_usd_path() -> str | None:
    for env_name in G1_ASSET_ENV_VARS:
        candidate = os.getenv(env_name, "").strip()
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _spawn_g1_reference(stage, g1_prim_path: str, g1_usd_path: str) -> bool:
    try:
        from pxr import UsdGeom
    except Exception:
        return False

    g1_xform = UsdGeom.Xform.Define(stage, g1_prim_path)
    g1_xform.GetPrim().GetReferences().AddReference(g1_usd_path)
    return True


def _spawn_g1_placeholder(stage, g1_prim_path: str) -> None:
    from pxr import Gf, UsdGeom

    g1_xform = UsdGeom.Xform.Define(stage, g1_prim_path)
    translate = g1_xform.AddTranslateOp()
    translate.Set(Gf.Vec3d(0.0, 0.0, 0.0))


def main() -> None:
    try:
        import omni.usd
        from pxr import Gf, UsdGeom
    except Exception as exc:
        raise RuntimeError(
            "Run this inside Isaac Sim Script Editor or with the Isaac Sim Python runtime."
        ) from exc

    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None:
        context.new_stage()
        stage = context.get_stage()

    # Isaac Sim APIs vary by version. This file is a version-tolerant skeleton, not a brittle
    # one-shot scene generator. Adjust prim creation and robot import calls to your Isaac release.
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    scene_objects = [
        {"name": "plastic_bottle", "object_type": "trash", "position": [1.1, 0.4, 0.8]},
        {"name": "paper_wrapper", "object_type": "trash", "position": [1.0, 0.1, 0.8]},
        {"name": "paper_cup", "object_type": "trash", "position": [0.9, -0.15, 0.8]},
        {"name": "dustbin", "object_type": "container", "position": [1.8, -0.4, 0.0]},
        {"name": "red_hazard_zone", "object_type": "hazard", "position": [0.2, 1.3, 0.0]},
        {"name": "unitree_g1", "object_type": "robot", "position": [0.0, 0.0, 0.0]},
    ]

    # TODO: Create or open the target stage on disk if you want scene persistence.
    # TODO: Create floor geometry and a table or work surface with the canonical prim names.
    # TODO: Add collision, rigid-body, and material properties to each trash object.
    # TODO: Prefer the real Unitree G1 USD asset from Isaac Lab, Isaac ROS Robots, or your
    # curated robot asset pipeline. This scaffold makes G1 the primary embodiment.
    # TODO: Add a virtual camera prim for later perception experiments.
    # TODO: Wire the Isaac ROS 2 bridge or action graph for /trashbot/groot_action handling.
    # TODO: Map incoming GR00T action vectors into G1 lower-body motion, upper-body end-effector
    # pose targets, and dexterous hand open/close control.

    for spec in scene_objects:
        if spec["object_type"] == "robot":
            continue
        prim_path = f"/World/{spec['name']}"
        if not stage.GetPrimAtPath(prim_path):
            xform = UsdGeom.Xform.Define(stage, prim_path)
            translate = xform.AddTranslateOp()
            translate.Set(Gf.Vec3d(*spec["position"]))

    g1_prim_path = os.getenv("G1_ROBOT_PRIM", DEFAULT_G1_PRIM_PATH)
    g1_usd_path = _resolve_g1_usd_path()
    if g1_usd_path:
        if _spawn_g1_reference(stage, g1_prim_path, g1_usd_path):
            print(f"Referenced Unitree G1 asset at {g1_usd_path} -> {g1_prim_path}")
        else:
            print("Unable to reference Unitree G1 asset with the current Isaac Python environment.")
            _spawn_g1_placeholder(stage, g1_prim_path)
    else:
        print(
            "No Unitree G1 USD asset found via G1_USD_PATH / UNITREE_G1_USD_PATH / "
            "GROOTKEEPER_G1_USD. Creating a placeholder prim at /World/G1 instead."
        )
        _spawn_g1_placeholder(stage, g1_prim_path)

    # TODO: If your Isaac Sim version provides the controller APIs you need, add:
    # - omni.isaac.core World setup
    # - G1 articulation handles
    # - whole-body control or upper-body IK for G1
    # - an execution loop driven by ROS 2 or the action graph
    _publish_scene_state_if_ros2_available(scene_objects)
    context.save_as_stage("trashbot_scene.usda")
    print("Trashbot Isaac scene skeleton created with Unitree G1 as the target embodiment.")


if __name__ == "__main__":
    main()
