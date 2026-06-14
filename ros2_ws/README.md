# ROS 2 Workspace

This workspace hosts the thin ROS 2 bridge nodes used by `grootkeeper`.

Build on the GB10:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
cd ros2_ws
colcon build
source install/setup.bash
```

Relevant topics:

- `/trashbot/groot_action`
- `/trashbot/scene_state`
- `/trashbot/execution_log`
