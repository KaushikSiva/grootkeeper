# Isaac Sim ROS 2 Bridge Notes

Enable the Isaac Sim ROS 2 bridge on the GB10 runtime:

1. Enable `omni.isaac.ros2_bridge`.
2. Make sure `ROS_DOMAIN_ID` matches `TRASHBOT_ROS_DOMAIN_ID` from `.env`.
3. Use ROS 2 Humble or Jazzy consistently across the backend shell and Isaac Sim shell.
4. Verify topic visibility with `ros2 topic list`.

Expected topics:

- `/trashbot/groot_action`
- `/trashbot/scene_state`
- `/trashbot/execution_log`

First-pass recommendation:

- Publish scene state from Isaac Sim as JSON over `std_msgs/msg/String`.
- Subscribe to `/trashbot/groot_action` in Isaac Sim and map primitives before attempting action-vector control.
