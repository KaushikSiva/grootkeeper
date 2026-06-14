from __future__ import annotations

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class IsaacExecutionListener(Node):
    def __init__(self) -> None:
        super().__init__("isaac_execution_listener")
        self.subscription = self.create_subscription(
            String,
            "/trashbot/groot_action",
            self.on_action,
            10,
        )

    def on_action(self, msg: String) -> None:
        self.get_logger().info(f"Received /trashbot/groot_action: {msg.data}")
        # TODO: Parse the JSON payload and map primitives to the Isaac Sim robot controller.
        # TODO: Convert target and destination names into stage prims or planner waypoints.
        # TODO: Publish /trashbot/execution_log updates after each robot action completes.


def main() -> None:
    rclpy.init()
    node = IsaacExecutionListener()
    try:
        node.get_logger().info("Listening on /trashbot/groot_action")
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
