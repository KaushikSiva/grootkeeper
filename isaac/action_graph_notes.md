# Isaac Action Graph Notes

Suggested action graph wiring:

1. `On Playback Tick`
2. `ROS2 Subscribe` on `/trashbot/groot_action`
3. JSON action parser node or Python node
4. Robot target selection and waypoint lookup
5. `Articulation Controller` for arm or mobile manipulator
6. Gripper open/close node
7. `ROS2 Publish` on `/trashbot/execution_log`

Implementation notes:

- Keep target object names aligned with the backend scene-state schema.
- Map `navigate`, `pick`, and `place` primitives before attempting dense action-vector playback.
- Use execution-log publishing so the dashboard can distinguish ROS publish success from actual Isaac execution.
