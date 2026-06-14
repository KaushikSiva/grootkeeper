# L3 Checkpoints

Checkpoint 1:

- `nvidia-smi` works.

Checkpoint 2:

- CUDA 12.6+ or a compatible environment is confirmed.

Checkpoint 3:

- Isaac-GR00T repo is cloned.

Checkpoint 4:

- GR00T install is complete using the official instructions.

Checkpoint 5:

- `python backend/groot_smoke_test.py` imports GR00T.

Checkpoint 6:

- ROS 2 works.

Checkpoint 7:

- Isaac Sim launches.

Checkpoint 8:

- ROS 2 bridge is enabled in Isaac Sim.

Checkpoint 9:

- `ros2 topic list` shows the trashbot topics.

Checkpoint 10:

- Backend `/plan` calls GR00T and returns actions.

Checkpoint 11:

- Backend `/execute_l3` publishes actions to ROS 2.

Checkpoint 12:

- Isaac listener receives actions.

Checkpoint 13:

- Isaac robot executes pick/drop.
