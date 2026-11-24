from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='smart_vacuum_control',
            executable='hardware_driver_node',
            name='vacuum_hardware_driver',
            output='screen',
        ),
        Node(
            package='smart_vacuum_control',
            executable='map_loader_node',
            name='map_loader',
            output='screen',
        ),
        Node(
            package='smart_vacuum_control',
            executable='task_manager_node',
            name='task_manager',
            output='screen',
        ),
    ])