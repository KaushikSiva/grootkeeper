# Unitree G1 Integration Notes

Use `Unitree G1` as the default robot embodiment in Isaac Sim for this repo.

Recommended asset sources:

- A curated `USD` exported into your Isaac Sim asset tree and referenced via `G1_USD_PATH`
- NVIDIA Isaac ROS / robot-description workflows for Unitree G1
- Isaac Lab / Unitree simulation assets when their path and version match your Isaac Sim install

Environment variables:

- `G1_USD_PATH`: absolute path to the G1 `USD` asset to reference in the scene
- `G1_ROBOT_PRIM`: stage prim path for the robot, default `/World/G1`
- `G1_EMBODIMENT_MODE`: recommended starting value `fixed_upper_body_pick_place`

MVP recommendation:

1. Start with `fixed_upper_body_pick_place`
2. Keep the lower body stable or fixed
3. Map `pick` and `place` to upper-body IK or scripted end-effector motion
4. Add `navigate` only after object grasp and drop are reliable

Useful G1 execution modes:

- `fixed_upper_body_pick_place`
- `stance_locked_reach_grasp`
- `locomanipulation`

Do not pretend whole-body Unitree G1 control is solved by a generic manipulator controller. The integration boundary is explicit in:

- `isaac/create_trashbot_scene.py`
- `ros2_ws/src/trashbot_bridge/trashbot_bridge/isaac_execution_listener.py`
