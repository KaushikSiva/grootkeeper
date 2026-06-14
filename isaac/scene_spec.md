# Trashbot Scene Spec

Required objects and canonical names:

- `plastic_bottle` with `object_type=trash`
- `paper_wrapper` with `object_type=trash`
- `paper_cup` with `object_type=trash`
- `dustbin` with `object_type=container`
- `red_hazard_zone` with `object_type=hazard`
- `unitree_g1` with `object_type=robot`

Scene goals:

- Use `Unitree G1` as the primary simulated robot.
- For MVP, prefer a stable fixed-base or stance-locked upper-body pick-and-place loop before free locomotion.
- The robot can reach the trash objects from its starting pose or staged waypoint pose.
- The dustbin is visible and reachable.
- The hazard zone is excluded from target selection in safety checks.
- A virtual camera can be added later, but the first MVP uses Isaac object poses directly.

Recommended stage conventions:

- Robot prim path: `/World/G1`
- Environment variable for the USD asset: `G1_USD_PATH`
- Scene-state robot object name: `unitree_g1`
