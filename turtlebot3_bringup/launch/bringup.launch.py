import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import ExecuteProcess
from launch_ros.actions import Node, SetParameter
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    bringup_dir = get_package_share_directory("turtlebot3_bringup")

    namespace = LaunchConfiguration("namespace", default="")
    usb_port = LaunchConfiguration("usb_port", default="/dev/ttyACM0")
    use_sim_time = LaunchConfiguration("use_sim_time", default="false")
    fps = LaunchConfiguration("fps", default="10.0")
    jpeg_quality = LaunchConfiguration("jpeg_quality", default="80") # Rolls to 95 when unset

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

    camera = GroupAction(
        actions=[
            SetParameter(
                name="camera.image_raw.compressed.jpeg_quality",
                value=ParameterValue(jpeg_quality, value_type=int),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup_dir, "launch", "camera.launch.py")
                ),
                launch_arguments={
                    "width": "640",
                    "height": "480",
                    "camera_info_url": "package://turtlebot3_bringup/config/camera_info.yaml",
                }.items(),
            ),
        ]
    )

    camera_throttle = Node(
        package="topic_tools",
        executable="throttle",
        name="camera_throttle",
        arguments=["messages", "/camera/image_raw/compressed", fps],
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
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace", default_value="", description="Namespace for nodes"
            ),
            robot,
            camera,
            camera_throttle,
            watchdog,
            twist_mux,
        ]
    )
