import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String
from smart_vacuum_interfaces.srv import SetFloorLevel


FLOOR_MAPS = {
    'Floor_1': {
        'grid_size': (10, 10),
        'initial_pose': (0.0, 0.0, 0.0),
        'description': 'Ground floor (Living Room, Kitchen, Hallway)',
    },
    'Floor_2': {
        'grid_size': (12, 12),
        'initial_pose': (1.5, 2.0, 1.57),
        'description': 'Upper floor (Master Bedroom, Guest Room, Study, Bathroom)',
    },
    'Basement': {
        'grid_size': (8, 8),
        'initial_pose': (0.5, -1.0, 3.14),
        'description': 'Lower level (Garage, Laundry Room)',
    },
}


class MapLoaderNode(Node):
    def __init__(self):
        super().__init__('map_loader')

        # Declare initial pose & floor parameters (default: Floor_1)
        self.declare_parameter('current_floor', 'Floor_1')
        self.declare_parameter('initial_x', 0.0)
        self.declare_parameter('initial_y', 0.0)
        self.declare_parameter('initial_theta', 0.0)

        self.current_floor = 'Floor_1'
        self.loaded_grid_map = self._generate_grid_map(*FLOOR_MAPS['Floor_1']['grid_size'])

        # Service server for switching floor maps
        self.srv_ = self.create_service(
            SetFloorLevel,
            '/vacuum/set_floor_level',
            self.handle_set_floor,
        )

        # Publish currently active floor so task_manager stays in sync
        self.floor_pub_ = self.create_publisher(String, '/vacuum/current_floor', 10)
        self.timer_ = self.create_timer(1.0, self.publish_current_floor)

        self.get_logger().info(
            'Map Loader ready. Service /vacuum/set_floor_level active (default: Floor_1).'
        )

    def _generate_grid_map(self, rows, cols):
        # Simulated 2D occupancy grid (0 = free space)
        return [[0 for _ in range(cols)] for _ in range(rows)]

    def publish_current_floor(self):
        msg = String()
        msg.data = self.current_floor
        self.floor_pub_.publish(msg)

    def handle_set_floor(self, request, response):
        floor_id = request.floor_id.strip()
        self.get_logger().info(f'Received request to load floor: "{floor_id}"')

        if floor_id not in FLOOR_MAPS:
            available = ', '.join(FLOOR_MAPS.keys())
            response.success = False
            response.message = f'Unknown floor "{floor_id}". Available floors: {available}.'
            response.initial_x = 0.0
            response.initial_y = 0.0
            response.initial_theta = 0.0
            self.get_logger().warn(response.message)
            return response

        floor_info = FLOOR_MAPS[floor_id]
        rows, cols = floor_info['grid_size']
        x, y, theta = floor_info['initial_pose']

        # Load simulated grid map into memory
        self.loaded_grid_map = self._generate_grid_map(rows, cols)
        self.current_floor = floor_id

        # Update ROS2 initial pose parameters
        self.set_parameters([
            Parameter('current_floor', Parameter.Type.STRING, floor_id),
            Parameter('initial_x', Parameter.Type.DOUBLE, float(x)),
            Parameter('initial_y', Parameter.Type.DOUBLE, float(y)),
            Parameter('initial_theta', Parameter.Type.DOUBLE, float(theta)),
        ])

        response.success = True
        response.message = (
            f'Loaded {rows}x{cols} grid map for {floor_id} '
            f'({floor_info["description"]}). Initial pose set to '
            f'(x={x}, y={y}, theta={theta}).'
        )
        response.initial_x = float(x)
        response.initial_y = float(y)
        response.initial_theta = float(theta)

        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = MapLoaderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()