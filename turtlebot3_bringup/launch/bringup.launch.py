import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    bringup_dir = get_package_share_directory("turtlebot3_bringup")

    namespace = LaunchConfiguration("namespace", default="")
    usb_port = LaunchConfiguration("usb_port", default="/dev/ttyACM0")
    use_sim_time = LaunchConfiguration("use_sim_time", default="false")

    robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "robot.launch.py")
        ),
        launch_arguments={
            "namespace": namespace,
            "usb_port": usb_port,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "camera.launch.py")
        ),
        launch_arguments={
            "width": "640",
            "height": "480",
            "camera_info_url": "package://turtlebot3_bringup/config/camera_info.yaml",
        }.items(),
    )

    twist_mux_config = os.path.join(
        get_package_share_directory("turtlebot3_bringup"), "config", "twist_mux.yaml"
    )

    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        name="twist_mux",
        output="screen",
        parameters=[twist_mux_config],
        remappings=[("cmd_vel_out", "cmd_vel")],
    )

    watchdog = ExecuteProcess(
        cmd=[
            "ros2",
            "topic",
            "pub",
            "-r",
            "20",
            "cmd_vel_watchdog",
            "geometry_msgs/msg/TwistStamped",
            "{}",
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace", default_value="", description="Namespace for nodes"
            ),
            DeclareLaunchArgument(
                "usb_port",
                default_value="/dev/ttyACM0",
                description="USB port for OpenCR",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use simulation clock",
            ),
            robot,
            camera,
            watchdog,
            twist_mux,
        ]
    )
