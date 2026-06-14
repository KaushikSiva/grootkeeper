# Demo Script

Primary line:

> We are not showing a toy adapter. This is the real L3 path: GR00T policy inference connected to Isaac Sim through ROS 2.

Suggested flow:

1. Show GB10 system status and confirm GPU, ROS 2, Isaac Sim, and GR00T checkpoints.
2. Show the Isaac scene objects and the Unitree G1 robot, and explain that perception is coming from the simulated world state first.
3. Send the command: `Pick up trash in the room and put it in the dustbin`.
4. Show the backend plan result and the ROS 2 publish.
5. Show Isaac Sim receiving the action and executing the task with the Unitree G1 embodiment.

Fallback phrase if the final controller mapping is still incomplete:

> Today we verified GR00T inference and ROS/Isaac command path separately; the remaining integration point is action-vector mapping to the Isaac robot controller.
