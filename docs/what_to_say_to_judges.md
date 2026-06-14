# What To Say To Judges

- Why Dell GB10:
  It is the local physical AI workstation that runs the actual robotics stack instead of outsourcing the critical path to the cloud.
- Why NVIDIA:
  The demo uses GR00T for robot policy inference, Isaac Sim for the simulated world, and ROS 2 bridging for execution.
- Why simulated first:
  The Isaac world is reproducible, debuggable, and safe while the embodiment and controller mapping are still being tuned.
- Why trash pickup:
  It is a long-horizon household manipulation task that requires scene understanding, sequencing, and controlled execution.
- What is real:
  The GR00T inference path, the ROS 2 publish path, and the Isaac Sim target scene are all first-class parts of the repo.
- Why Unitree G1:
  It gives the demo a serious humanoid embodiment for grasping and eventual locomanipulation instead of a generic placeholder robot.
- What is next:
  The remaining high-value step is action-vector mapping or post-training for the chosen robot embodiment.
