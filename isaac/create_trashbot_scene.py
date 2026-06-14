from __future__ import annotations

import json


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
        {"name": "robot_base", "object_type": "robot", "position": [0.0, 0.0, 0.0]},
    ]

    # TODO: Create or open the target stage on disk if you want scene persistence.
    # TODO: Create floor geometry and a table or work surface with the canonical prim names.
    # TODO: Add collision, rigid-body, and material properties to each trash object.
    # TODO: Spawn a mobile manipulator or articulated arm asset that matches your target embodiment.
    # TODO: Add a virtual camera prim for later perception experiments.
    # TODO: Wire the Isaac ROS 2 bridge or action graph for /trashbot/groot_action handling.
    # TODO: Map incoming GR00T action vectors into base motion, end-effector pose, and gripper control.

    for spec in scene_objects:
        prim_path = f"/World/{spec['name']}"
        if not stage.GetPrimAtPath(prim_path):
            xform = UsdGeom.Xform.Define(stage, prim_path)
            translate = xform.AddTranslateOp()
            translate.Set(Gf.Vec3d(*spec["position"]))

    # TODO: If your Isaac Sim version provides the controller APIs you need, add:
    # - omni.isaac.core World setup
    # - robot articulation handles
    # - an execution loop driven by ROS 2 or the action graph
    _publish_scene_state_if_ros2_available(scene_objects)
    context.save_as_stage("trashbot_scene.usda")
    print("Trashbot Isaac scene skeleton created. Review TODOs in isaac/create_trashbot_scene.py.")


if __name__ == "__main__":
    main()
