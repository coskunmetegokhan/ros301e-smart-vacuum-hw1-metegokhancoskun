import rclpy
from rclpy.node import Node
from smart_vacuum_interfaces.msg import VacuumStatus


class VacuumHardwareDriver(Node):
    def __init__(self):
        super().__init__('vacuum_hardware_driver')
        self.publisher_ = self.create_publisher(VacuumStatus, '/vacuum/status', 10)
        self.timer_ = self.create_timer(1.0, self.publish_status)  # 1 Hz

        self.battery_level = 100.0
        self.tick = 0
        self.get_logger().info('Vacuum Hardware Driver started. Publishing telemetry on /vacuum/status at 1 Hz.')

    def publish_status(self):
        self.tick += 1

        # Simulate gradual battery drain (and reset to 100% if it drops below 10%)
        self.battery_level = self.battery_level - 0.5
        if self.battery_level <= 10.0:
            self.battery_level = 100.0

        # Simulate dustbin filling up over time and occasional sensor triggers
        dustbin_status = 'FULL' if (self.tick % 60) >= 45 else 'OK'
        cliff_detected = (self.tick % 25 == 0)
        bumper_triggered = (self.tick % 10 == 0)

        msg = VacuumStatus()
        msg.battery_level = float(self.battery_level)
        msg.dustbin_status = dustbin_status
        msg.cliff_detected = cliff_detected
        msg.bumper_triggered = bumper_triggered

        self.publisher_.publish(msg)
        self.get_logger().info(
            f'Telemetry -> Battery: {msg.battery_level:.1f}% | '
            f'Dustbin: {msg.dustbin_status} | '
            f'Cliff: {msg.cliff_detected} | Bumper: {msg.bumper_triggered}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = VacuumHardwareDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()