# L3 Architecture

The real L3 path is:

User command  
→ backend  
→ Isaac scene state  
→ GR00T observation  
→ real GR00T inference  
→ safety  
→ ROS 2 topic  
→ Isaac Sim ROS 2 bridge  
→ simulated robot controller  
→ object moved to dustbin

Machine split:

- Mac: VS Code/Codex, GitHub push, SSH to GB10, browser dashboard.
- GB10: NVIDIA GPU runtime, Isaac-GR00T repo and checkpoint, FastAPI backend, ROS 2, Isaac Sim, ROS 2 bridge, and robot execution.

Design stance:

- This is GR00T-first, not adapter-first.
- The backend fails loudly if the real GR00T API is not wired.
- Scene perception comes from Isaac object poses first, then optional virtual camera later.
- Mock mode exists only as a diagnostic fallback and is blocked from real `/execute_l3`.
