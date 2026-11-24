import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'smart_vacuum_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='ROS2 nodes for the Autonomous Home Vacuum Cleaner',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hardware_driver_node = smart_vacuum_control.hardware_driver_node:main',
            'map_loader_node = smart_vacuum_control.map_loader_node:main',
            'task_manager_node = smart_vacuum_control.task_manager_node:main',
        ],
    },
)