from __future__ import annotations

from schemas import SceneObject, SceneState


def get_scene_state_from_isaac_placeholder() -> SceneState:
    # Replace this placeholder with a live Isaac Sim ROS 2 scene_state subscription
    # or an Isaac Python world query once the GB10 runtime is wired end-to-end.
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
                name="robot_base",
                object_type="robot",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
            ),
        ],
    )


def publish_expected_scene_to_ros_placeholder() -> dict[str, object]:
    # Replace this placeholder with ROS 2 publishing from Isaac Sim, either through the
    # ROS 2 bridge action graph or an Isaac-side Python node.
    return {
        "status": "placeholder_only",
        "notes": [
            "Publish /trashbot/scene_state from Isaac Sim once omni.isaac.ros2_bridge is enabled.",
            "Mirror the SceneState schema as JSON in std_msgs/String for the first integration pass.",
            "Move from this placeholder to live Isaac object pose output before the final demo.",
        ],
    }
