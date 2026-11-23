FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-ros-gz \
    && rm -rf /var/lib/apt/lists/*

# Official TurtleBot3 Burger simulation assets and the Nav2 baseline.
RUN apt-get update && apt-get install -y \
    ros-jazzy-nav2-bringup \
    ros-jazzy-turtlebot3-gazebo \
    ros-jazzy-turtlebot3-description \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/ros2_ws

RUN rosdep init || true

RUN printf '%s\n' \
    'source /opt/ros/jazzy/setup.bash' \
    'if [ -f /workspace/ros2_ws/install/setup.bash ]; then' \
    '    source /workspace/ros2_ws/install/setup.bash' \
    'fi' \
    >> /root/.bashrc

CMD ["bash"]
