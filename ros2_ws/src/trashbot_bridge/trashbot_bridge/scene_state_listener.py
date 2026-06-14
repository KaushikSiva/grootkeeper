from __future__ import annotations

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SceneStateListener(Node):
    def __init__(self) -> None:
        super().__init__("scene_state_listener")
        self.subscription = self.create_subscription(
            String,
            "/trashbot/scene_state",
            self.on_scene_state,
            10,
        )

    def on_scene_state(self, msg: String) -> None:
        self.get_logger().info(f"Received /trashbot/scene_state: {msg.data}")


def main() -> None:
    rclpy.init()
    node = SceneStateListener()
    try:
        node.get_logger().info("Listening on /trashbot/scene_state")
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
