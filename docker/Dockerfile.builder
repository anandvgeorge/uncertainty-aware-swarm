FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-ros-gz \
    ros-jazzy-turtlebot3-description \
    ros-jazzy-turtlebot3-gazebo \
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
