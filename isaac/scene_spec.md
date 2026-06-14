# Trashbot Scene Spec

Required objects and canonical names:

- `plastic_bottle` with `object_type=trash`
- `paper_wrapper` with `object_type=trash`
- `paper_cup` with `object_type=trash`
- `dustbin` with `object_type=container`
- `red_hazard_zone` with `object_type=hazard`
- `robot_base` with `object_type=robot`

Scene goals:

- The robot can reach the trash objects from its base pose.
- The dustbin is visible and reachable.
- The hazard zone is excluded from target selection in safety checks.
- A virtual camera can be added later, but the first MVP uses Isaac object poses directly.
