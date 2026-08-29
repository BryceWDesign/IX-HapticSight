# ROS 2 and Hardware Integration

The v0.2 ROS 2 layer intentionally uses standard interfaces where possible.

## Inputs

- `geometry_msgs/WrenchStamped` for force/torque
- `std_msgs/Bool` for E-stop state

## Outputs

- `geometry_msgs/TwistStamped` for already-bounded velocity commands
- `std_msgs/String` structured safety side-channel
- `control_msgs/FollowJointTrajectory` action client for standard trajectory controllers

The safety authority should run upstream of these outputs. Robot-specific code may reduce authority further, but it may not expand force or speed above the granted envelope.

ROS 2 is loaded lazily. A non-ROS machine can run the protocol, perception, control, evidence, simulation, and tests. Starting a ROS bridge without `rclpy` produces an explicit unavailable error rather than silently simulating hardware.
