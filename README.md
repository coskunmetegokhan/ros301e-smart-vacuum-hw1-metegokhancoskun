# ROS 301E — HW I: Autonomous Home Vacuum Cleaner (ROS2 Jazzy)

A ROS2 software architecture simulating an Autonomous Home Vacuum Cleaner using custom topics, services, and actions in Python (`rclpy`).

## Workspace Structure
- `src/smart_vacuum_interfaces/` (`ament_cmake`): Custom interface definitions:
  - `msg/VacuumStatus.msg` — 1 Hz telemetry (`battery_level`, `dustbin_status`, `cliff_detected`, `bumper_triggered`)
  - `srv/SetFloorLevel.srv` — Floor map & initial pose configuration (`floor_id` -> `success`, `message`, `initial_x/y/theta`)
  - `action/VacuumTask.action` — Multi-room cleaning/mapping execution (`mode`, `power_mode`, live feedback, result stats, and cancellation)
- `src/smart_vacuum_control/` (`ament_python`): Three ROS2 nodes + launch file:
  - `vacuum_hardware_driver` — Publishes `/vacuum/status` at 1 Hz
  - `map_loader` — Serves `/vacuum/set_floor_level`, updates initial pose parameters, publishes `/vacuum/current_floor`
  - `task_manager` — Subscribes to `/vacuum/status` and `/vacuum/current_floor`, runs `/vacuum/execute_task` action server with `MultiThreadedExecutor` for mid-task cancellation
  - `launch/vacuum_system.launch.py` — Launches all three nodes together

## Build & Run
```bash
source /opt/ros/jazzy/setup.bash
cd ~/smart_vacuum_ws
colcon build
source install/setup.bash
ros2 launch smart_vacuum_control vacuum_system.launch.py
