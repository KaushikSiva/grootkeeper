# grootkeeper

`grootkeeper` is a GR00T-first robotics demo repo for Dell GB10. The target command is:

> Pick up trash in the room and put it in the dustbin.

This repo is intentionally not adapter-only. The backend refuses to pretend that real NVIDIA Isaac-GR00T policy inference is wired when it is not. The main endpoint is `/execute_l3`.

Target simulated embodiment: `Unitree G1` in Isaac Sim.

## What Mac does

- VS Code / Codex development
- GitHub push
- Browser dashboard
- SSH into the GB10

## What GB10 does

- NVIDIA driver and CUDA verification
- Isaac-GR00T repo and checkpoint access
- FastAPI backend
- ROS 2 Humble or Jazzy
- Isaac Sim
- Isaac Sim ROS 2 bridge
- GR00T inference client
- Isaac / ROS execution path

## Prereqs on GB10

- NVIDIA GPU drivers working
- CUDA-compatible environment for the GR00T install path
- ROS 2 Humble or Jazzy installed
- Isaac Sim installed
- Isaac-GR00T cloned and installed using the official NVIDIA instructions
- Access to the configured GR00T checkpoint
- A Unitree G1 USD asset path available for Isaac Sim and set in `G1_USD_PATH`

## Step 1: push repo from Mac

```bash
git add .
git commit -m "Build GrootKeeper"
git push
```

## Step 2: SSH to GB10

Exact SSH point:

```bash
ssh <user>@<gb10-ip>
```

## Step 3: run GPU check

## Step 4: clone/install Isaac-GR00T using official docs

## Step 5: run GR00T smoke test

## Step 6: check ROS 2

## Step 7: check Isaac Sim

## Step 8: build ROS 2 workspace

## Step 9: run backend in GR00T mode

## Step 10: open dashboard from Mac

This README step is not the same thing as `./scripts/10_test_groot_plan.sh`.

## Step 11: execute

### On GB10

```bash
git clone <repo-url> grootkeeper
cd grootkeeper
cp configs/env.example .env
chmod +x scripts/*.sh
./scripts/01_check_gb10_gpu.sh
./scripts/02_setup_python_env.sh
./scripts/03_clone_or_check_groot.sh
# follow official Isaac-GR00T install instructions
./scripts/04_groot_smoke_test.sh
./scripts/05_check_ros2.sh
./scripts/06_check_isaac_sim.sh
./scripts/07_build_ros2_ws.sh
./scripts/08a_run_groot_policy_server.sh
./scripts/08_run_backend_groot.sh
```

In another GB10 terminal:

```bash
cd grootkeeper
./scripts/09_test_backend_status.sh
# Real GR00T planning test. Requires backend/groot_client.py to be wired
# to a running NVIDIA Isaac-GR00T policy server.
./scripts/10_test_groot_plan.sh
# Deterministic diagnostic path. Requires exporting GROOT_SMOKE_ONLY=1
# before starting the backend in the first terminal.
./scripts/10_test_groot_smoke.sh
```

### On Mac

```bash
open frontend/dashboard.html
```

Set backend URL to:

```text
http://<gb10-ip>:8000
```

## Where the real integration points are

- `backend/groot_client.py`
  This is the policy-server client adapter. It converts scene/image/proprio inputs into the official GR00T observation schema and decodes returned action chunks.
- `backend/task_orchestrator.py`
  This enforces the GR00T-first path, safety gate, and ROS 2 publish flow.
- `ros2_ws/src/trashbot_bridge/trashbot_bridge/isaac_execution_listener.py`
  This is where GR00T actions must be mapped to the Unitree G1 Isaac controller.
- `isaac/create_trashbot_scene.py`
  This is the Isaac-side skeleton for the scene, Unitree G1 asset reference, camera, and scene-state publishing.

## What can fail and how to debug

- Run `./scripts/checkpoint_all_l3.sh` for the loud checkpoint sweep.
- Read `docs/l3_checkpoints.md` for verification order.
- Read `docs/failure_debugging.md` for the common failure cases.
- If `/status` says the policy server is unavailable, start `./scripts/08a_run_groot_policy_server.sh` and verify `GROOT_SERVER_HOST` / `GROOT_SERVER_PORT`.
- If `/system/status` shows `groot_server_ok=false`, the backend cannot reach the GR00T ZeroMQ server yet.

## Command Summary

Mac:

```bash
git add .
git commit -m "Build GrootKeeper"
git push
ssh <user>@<gb10-ip>
```

GB10:

```bash
git clone <repo-url> grootkeeper
cd grootkeeper
cp configs/env.example .env
chmod +x scripts/*.sh
./scripts/01_check_gb10_gpu.sh
./scripts/02_setup_python_env.sh
./scripts/03_clone_or_check_groot.sh
./scripts/04_groot_smoke_test.sh
./scripts/05_check_ros2.sh
./scripts/06_check_isaac_sim.sh
./scripts/07_build_ros2_ws.sh
./scripts/08_run_backend_groot.sh
```
