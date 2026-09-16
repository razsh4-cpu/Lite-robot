from setuptools import find_packages, setup

package_name = 'lite3_security_patrol'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/control_bridge.yaml', 'config/nav2_lite3_template.yaml', 'config/odometry_experiments.yaml', 'config/sensor_extrinsics.yaml', 'config/patrol_waypoints.template.yaml']),
        ('share/' + package_name + '/launch', ['launch/patrol_scaffold.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={'console_scripts': [
        'cmd_vel_normalizer = lite3_security_patrol.cmd_vel_normalizer:main',
    ]},
)
