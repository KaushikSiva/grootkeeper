from __future__ import annotations

import json
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class GrootActionPublisher(Node):
    def __init__(self) -> None:
        super().__init__("groot_action_publisher")
        self.publisher = self.create_publisher(String, "/trashbot/groot_action", 10)

    def publish_payload(self, payload: str) -> None:
        message = String()
        message.data = payload
        self.publisher.publish(message)
        self.get_logger().info(f"Published /trashbot/groot_action: {payload}")


def main() -> None:
    rclpy.init()
    node = GrootActionPublisher()
    try:
        payload = (
            sys.argv[1]
            if len(sys.argv) > 1
            else json.dumps(
                {
                    "source": "trashbot_bridge.groot_action_publisher",
                    "actions": [{"primitive": "pick", "target": "plastic_bottle"}],
                }
            )
        )
        node.publish_payload(payload)
        rclpy.spin_once(node, timeout_sec=0.2)
    finally:
        node.destroy_node()
        rclpy.shutdown()
