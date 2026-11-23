cmake_minimum_required(VERSION 3.8)
project(swarm_bringup)

find_package(ament_cmake REQUIRED)

# Gazebo runs in a separate container and reads these meshes from the shared
# install volume. Use the official TurtleBot3 model resources.
# Locate assets directly: the upstream 2.3.7 CMake config exports a legacy
# Gazebo Classic dependency even though we only use its Harmonic resources.
ament_index_get_prefix_path(ament_prefixes)
find_path(tb3_share
  NAMES models/turtlebot3_burger/model.sdf
  PATHS ${ament_prefixes}
  PATH_SUFFIXES share/turtlebot3_gazebo
  NO_DEFAULT_PATH)
if(NOT tb3_share)
  message(FATAL_ERROR "Install turtlebot3_gazebo to provide the Burger model assets")
endif()
install(DIRECTORY
  "${tb3_share}/models/turtlebot3_burger"
  "${tb3_share}/models/turtlebot3_common"
  DESTINATION share/${PROJECT_NAME}/simulation)
install(DIRECTORY launch worlds DESTINATION share/${PROJECT_NAME})

ament_package()
