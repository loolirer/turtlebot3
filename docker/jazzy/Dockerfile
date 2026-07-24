# Use the base ROS2 jazzy image
FROM ros:jazzy-ros-base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV COLCON_WS=/root/turtlebot3_ws

# Install the required packages in a single layer and clean up afterwards
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-argcomplete \
    python3-colcon-common-extensions \
    libboost-system-dev \
    build-essential \
    cmake \
    libudev-dev \
    udev \
    git \
    nano \
    ros-${ROS_DISTRO}-cartographer \
    ros-${ROS_DISTRO}-cartographer-ros \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-nav2-route \
    ros-${ROS_DISTRO}-turtlebot3-msgs \
    ros-${ROS_DISTRO}-dynamixel-sdk \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-hls-lfcd-lds-driver \
    ros-${ROS_DISTRO}-ld08-driver \
    ros-${ROS_DISTRO}-coin-d4-driver \
    ros-${ROS_DISTRO}-urdf \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    ros-${ROS_DISTRO}-compressed-image-transport \
    ros-${ROS_DISTRO}-topic-tools \
    ros-${ROS_DISTRO}-twist-mux \
    && rm -rf /var/lib/apt/lists/*

# --- Raspberry Pi camera stack, built FROM SOURCE (single, matched libcamera) ---
# Not the stock apt camera_ros: that pulls a second libcamera, and because the container
# runs as root libcamera isolates the camera IPA into a separate proxy process which then
# mismatches the main process and crashes deserializing the ControlInfoMap ("A list of
# V4L2 controls requires a ControlInfoMap"). Building ONE libcamera (the Raspberry Pi
# fork, proven on this robot) + camera_ros against it keeps a single matched libcamera —
# the way it worked natively. Refs are ARGs so the pair can be bumped if they drift.
ARG LIBCAMERA_REF=v0.5.2
ARG CAMERA_ROS_REF=main

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    meson ninja-build \
    python3-jinja2 python3-yaml python3-ply pybind11-dev \
    libgnutls28-dev openssl libtiff-dev \
    libglib2.0-dev libgstreamer-plugins-base1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# libcamera -> /usr/local (multiarch libdir forced; the Pi is arm64), then registered
# with ldconfig so BOTH the camera node and the isolated IPA proxy resolve this one .so.
# PKG_CONFIG_PATH lets camera_ros' pkg-config discovery find it at build time.
ENV LIBCAMERA_LIBDIR=/usr/local/lib/aarch64-linux-gnu
ENV PKG_CONFIG_PATH=${LIBCAMERA_LIBDIR}/pkgconfig
WORKDIR /root
RUN git clone -b ${LIBCAMERA_REF} --depth 1 https://github.com/raspberrypi/libcamera.git && \
    cd libcamera && \
    meson setup build --buildtype=release --libdir=lib/aarch64-linux-gnu \
      -Dpipelines=rpi/vc4,rpi/pisp -Dipas=rpi/vc4,rpi/pisp -Dv4l2=true \
      -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled \
      -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled && \
    ninja -C build install && \
    echo "${LIBCAMERA_LIBDIR}" > /etc/ld.so.conf.d/libcamera.conf && ldconfig

# --- Workspace: turtlebot3 fork + camera_ros, built against the source libcamera ---
WORKDIR ${COLCON_WS}
RUN mkdir -p ${COLCON_WS}/src
COPY . ${COLCON_WS}/src/turtlebot3
RUN git clone -b ${CAMERA_ROS_REF} --depth 1 \
    https://github.com/christianrauch/camera_ros.git src/camera_ros
# Pull only camera_ros' ROS deps (camera_info_manager, cv_bridge, diagnostic_msgs, …):
# skip `libcamera` (ours, from source) and `image_view` (the bringup never enables it).
# rosdep scoped to src/camera_ros so it can't drag the turtlebot3 metapackages' nav2 /
# cartographer exec-deps back in.
RUN apt-get update && \
    (rosdep init 2>/dev/null || true) && rosdep update --rosdistro ${ROS_DISTRO} && \
    rosdep install -y --from-paths src/camera_ros --ignore-src \
      --rosdistro ${ROS_DISTRO} --skip-keys="libcamera image_view" && \
    rm -rf /var/lib/apt/lists/*
RUN bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd ${COLCON_WS} && \
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release"

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc && \
    echo "source ${COLCON_WS}/install/setup.bash" >> ~/.bashrc && \
    echo "alias cb='colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release'" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=30 # TURTLEBOT3" >> ~/.bashrc && \
    echo "# export TURTLEBOT3_MODEL= # burger, waffle, waffle_pi" >> ~/.bashrc && \
    echo "# export LDS_MODEL= # LDS-01, LDS-02, LDS-03" >> ~/.bashrc

CMD ["bash"]
