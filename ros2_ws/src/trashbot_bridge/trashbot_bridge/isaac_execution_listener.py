from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class IsaacExecutionListener(Node):
    def __init__(self) -> None:
        super().__init__("isaac_execution_listener")
        self.execution_publisher = self.create_publisher(String, "/trashbot/execution_log", 10)
        self.subscription = self.create_subscription(
            String,
            "/trashbot/groot_action",
            self.on_action,
            10,
        )

    def on_action(self, msg: String) -> None:
        self.get_logger().info(f"Received /trashbot/groot_action: {msg.data}")
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().error(f"Invalid groot_action JSON: {exc}")
            return

        actions = payload.get("actions", [])
        embodiment_mode = payload.get("embodiment_mode", "unitree_g1")
        execution_summary = {
            "robot": "unitree_g1",
            "embodiment_mode": embodiment_mode,
            "received_actions": len(actions),
            "execution_intents": self._build_g1_execution_intents(actions),
        }
        self._publish_execution_log(execution_summary)

        # TODO: Replace the intent summary with real Isaac Sim controller calls for Unitree G1.
        # TODO: Convert target and destination names into G1 approach poses and hand trajectories.
        # TODO: Route navigate to lower-body locomotion only after stance stability is validated.

    def _build_g1_execution_intents(self, actions: list[dict]) -> list[dict[str, str]]:
        intents: list[dict[str, str]] = []
        for action in actions:
            primitive = action.get("primitive", "unknown")
            target = action.get("target", "")
            destination = action.get("destination", "")

            if primitive == "navigate":
                intents.append(
                    {
                        "primitive": primitive,
                        "g1_mode": "lower_body_waypoint_or_stance_shift",
                        "target": target or destination,
                    }
                )
            elif primitive == "pick":
                intents.append(
                    {
                        "primitive": primitive,
                        "g1_mode": "upper_body_reach_and_hand_close",
                        "target": target,
                    }
                )
            elif primitive in {"place", "drop", "release"}:
                intents.append(
                    {
                        "primitive": primitive,
                        "g1_mode": "upper_body_approach_and_hand_open",
                        "target": destination or target,
                    }
                )
            else:
                intents.append(
                    {
                        "primitive": primitive,
                        "g1_mode": "custom_action_vector_mapping_required",
                        "target": target or destination,
                    }
                )
        return intents

    def _publish_execution_log(self, payload: dict[str, object]) -> None:
        message = String()
        message.data = json.dumps(payload)
        self.execution_publisher.publish(message)
        self.get_logger().info(f"Published /trashbot/execution_log: {message.data}")


def main() -> None:
    rclpy.init()
    node = IsaacExecutionListener()
    try:
        node.get_logger().info("Listening on /trashbot/groot_action")
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
