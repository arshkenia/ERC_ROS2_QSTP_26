cmake_minimum_required(VERSION 3.8)
project(waypoint_follower)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/Mission.action"
  DEPENDENCIES geometry_msgs nav_msgs
)

# 3. Install Python scripts as executables (renaming them to drop the .py)
install(PROGRAMS
  scripts/mission_server.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME mission_server
)

install(PROGRAMS
  scripts/mission_client.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME mission_client
)

# 4. Install the missions directory to the share directory
install(DIRECTORY
  missions
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
