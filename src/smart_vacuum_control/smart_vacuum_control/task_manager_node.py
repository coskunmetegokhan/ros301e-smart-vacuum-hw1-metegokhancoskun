import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String
from smart_vacuum_interfaces.msg import VacuumStatus
from smart_vacuum_interfaces.action import VacuumTask


VALID_MODES = {'MAP_ONLY', 'CLEAN_EXISTING_MAP', 'SLAM_AND_CLEAN'}
VALID_POWER_MODES = {'ECO', 'STANDARD', 'TURBO'}

FLOOR_ROOMS = {
    'Floor_1': ['Living Room', 'Kitchen', 'Hallway'],
    'Floor_2': ['Master Bedroom', 'Guest Room', 'Study', 'Bathroom'],
    'Basement': ['Garage', 'Laundry Room'],
}

# Simulated area cleaned per step (m^2) by power mode
AREA_RATE_BY_POWER = {
    'ECO': 1.2,
    'STANDARD': 1.8,
    'TURBO': 2.5,
}


class TaskManagerNode(Node):
    def __init__(self):
        super().__init__('task_manager')
        self.cb_group = ReentrantCallbackGroup()

        # Track latest telemetry and active floor
        self.latest_battery = 100.0
        self.latest_dustbin = 'OK'
        self.current_floor = 'Floor_1'

        self.status_sub_ = self.create_subscription(
            VacuumStatus,
            '/vacuum/status',
            self.status_callback,
            10,
            callback_group=self.cb_group,
        )

        self.floor_sub_ = self.create_subscription(
            String,
            '/vacuum/current_floor',
            self.floor_callback,
            10,
            callback_group=self.cb_group,
        )

        self.action_server_ = ActionServer(
            self,
            VacuumTask,
            '/vacuum/execute_task',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.cb_group,
        )

        self.get_logger().info('Task Manager ready. Action server active on /vacuum/execute_task.')

    def status_callback(self, msg):
        self.latest_battery = msg.battery_level
        self.latest_dustbin = msg.dustbin_status

    def floor_callback(self, msg):
        self.current_floor = msg.data

    def goal_callback(self, goal_request):
        if goal_request.mode not in VALID_MODES:
            self.get_logger().warn(f'Rejected invalid mode: "{goal_request.mode}"')
            return GoalResponse.REJECT
        if goal_request.power_mode not in VALID_POWER_MODES:
            self.get_logger().warn(f'Rejected invalid power_mode: "{goal_request.power_mode}"')
            return GoalResponse.REJECT

        self.get_logger().info(
            f'Accepted goal -> floor: {self.current_floor}, '
            f'mode: {goal_request.mode}, power_mode: {goal_request.power_mode}'
        )
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Cancel request received (Return to Dock). Accepting cancellation...')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        mode = goal_handle.request.mode
        power_mode = goal_handle.request.power_mode
        rooms = FLOOR_ROOMS.get(self.current_floor, ['Main Area'])

        steps_per_room = 4
        total_steps = len(rooms) * steps_per_room
        completed_steps = 0
        total_area = 0.0
        start_time = time.time()

        feedback_msg = VacuumTask.Feedback()
        result = VacuumTask.Result()

        for room in rooms:
            for _ in range(steps_per_room):
                # Check for mid-task cancellation (Return to Dock)
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result.total_area_cleaned_m2 = round(total_area, 2)
                    result.elapsed_time_sec = round(time.time() - start_time, 2)
                    result.completion_code = 'CANCELED_RETURN_TO_DOCK'
                    self.get_logger().info(
                        f'Task canceled gracefully in {room}. Returning to dock. '
                        f'Area cleaned: {result.total_area_cleaned_m2} m^2, '
                        f'Elapsed: {result.elapsed_time_sec} s.'
                    )
                    return result

                time.sleep(1.0)
                completed_steps += 1

                # Only accumulate cleaned area when cleaning is enabled
                if mode != 'MAP_ONLY':
                    total_area += AREA_RATE_BY_POWER[power_mode]

                feedback_msg.current_room = room
                feedback_msg.completion_percentage = round((completed_steps / total_steps) * 100.0, 1)
                feedback_msg.battery_level = float(self.latest_battery)
                goal_handle.publish_feedback(feedback_msg)

                self.get_logger().info(
                    f'[{mode} | {power_mode}] Room: {feedback_msg.current_room} | '
                    f'Progress: {feedback_msg.completion_percentage}% | '
                    f'Battery: {feedback_msg.battery_level:.1f}%'
                )

        goal_handle.succeed()
        result.total_area_cleaned_m2 = round(total_area, 2)
        result.elapsed_time_sec = round(time.time() - start_time, 2)
        result.completion_code = 'COMPLETED'
        self.get_logger().info(
            f'Task completed! Area: {result.total_area_cleaned_m2} m^2, '
            f'Elapsed: {result.elapsed_time_sec} s.'
        )
        return result


def main(args=None):
    rclpy.init(args=args)
    node = TaskManagerNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()