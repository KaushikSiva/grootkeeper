# Failure Debugging

Common failures and what to check next:

- `nvidia-smi` missing:
  The NVIDIA driver stack is not healthy on the GB10. Fix this before touching GR00T or Isaac Sim.
- CUDA mismatch:
  Check `nvcc --version`, the GR00T install instructions, and any CUDA-dependent Python packages.
- GR00T import failure:
  Confirm `GROOT_REPO_DIR`, the Python environment, and editable installs from the official repo instructions.
- Hugging Face checkpoint auth/download issue:
  Confirm you are logged in, have access to the checkpoint, and that `GROOT_CHECKPOINT` is valid.
- Python version mismatch:
  The interpreter used by `.venv`, GR00T, and Isaac tools must match the supported versions.
- Isaac Sim python path missing:
  Set `ISAAC_SIM_PYTHON` to Isaac Sim's `python.sh` on the GB10.
- `ROS_DOMAIN_ID` mismatch:
  The backend shell, ROS 2 terminals, and Isaac Sim bridge must share the same domain ID.
- ROS 2 bridge disabled:
  Enable `omni.isaac.ros2_bridge` and restart Isaac Sim.
- `ros2 topic pub` works but Isaac does not receive:
  Check bridge enablement, topic names, domain ID, and whether the action graph or listener node is actually running.
- GR00T action output not matching the robot controller:
  Open `backend/groot_client.py` and `ros2_ws/src/trashbot_bridge/trashbot_bridge/isaac_execution_listener.py` and align the action schema.
- Object pose mismatch:
  Confirm Isaac stage object names and positions match the backend scene-state schema.
