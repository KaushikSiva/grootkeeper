# Isaac Action Graph Notes

Suggested action graph wiring:

1. `On Playback Tick`
2. `ROS2 Subscribe` on `/trashbot/groot_action`
3. JSON action parser node or Python node
4. Unitree G1 target selection and waypoint lookup
5. `Articulation Controller` or Python control node for G1 upper-body / whole-body motion
6. Hand open/close node for the chosen G1 hand embodiment
7. `ROS2 Publish` on `/trashbot/execution_log`

Implementation notes:

- Keep target object names aligned with the backend scene-state schema.
- Map `navigate`, `pick`, and `place` primitives before attempting dense action-vector playback.
- For MVP, route `navigate` to staged G1 stance or waypoint motion and keep `pick` / `place` on upper-body control.
- Publish the active G1 embodiment mode such as `fixed_upper_body_pick_place` or `locomanipulation`.
- Use execution-log publishing so the dashboard can distinguish ROS publish success from actual Isaac execution.
