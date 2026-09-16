cmake_minimum_required(VERSION 3.8)
project(sensor_visualization)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(lite3_control_safety test/test_lite3_control_safety.py)
endif()

set(LITE3_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../Lite3_MotionSDK")
set(LITE3_SDK_LIB "${LITE3_SDK_DIR}/lib/libdeeprobotics_legged_sdk_x86_64.so")

add_executable(lite3_telemetry_bridge src/lite3_telemetry_bridge.cpp)
target_include_directories(lite3_telemetry_bridge PRIVATE
  "${LITE3_SDK_DIR}/include"
  "${LITE3_SDK_DIR}/include/common")
ament_target_dependencies(lite3_telemetry_bridge rclcpp sensor_msgs geometry_msgs)
target_link_libraries(lite3_telemetry_bridge "${LITE3_SDK_LIB}")
set_target_properties(lite3_telemetry_bridge PROPERTIES
  BUILD_RPATH "${LITE3_SDK_DIR}/lib"
  INSTALL_RPATH "$ORIGIN/..")

install(DIRECTORY launch rviz config urdf DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/plan_from_rviz_goal.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME plan_from_rviz_goal)
install(PROGRAMS scripts/lidar_odom_motion_monitor.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lidar_odom_motion_monitor)
install(PROGRAMS scripts/xbox_teleop_dry_run.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME xbox_teleop_dry_run)
install(PROGRAMS scripts/xbox_lite3_motion_host_bridge.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME xbox_lite3_motion_host_bridge)
install(PROGRAMS scripts/lite3_telemetry_watchdog.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_telemetry_watchdog)
install(PROGRAMS scripts/lite3_manual_axis_control.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_manual_axis_control)
install(PROGRAMS scripts/lite3_cmd_vel_adapter.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_cmd_vel_adapter)
install(PROGRAMS scripts/lite3_xbox_cmd_vel_teleop.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_xbox_cmd_vel_teleop)
install(PROGRAMS scripts/lite3_control_logger.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_control_logger)
install(PROGRAMS scripts/lite3_cmd_vel_arbiter.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_cmd_vel_arbiter)
install(PROGRAMS scripts/lite3_keyboard_cmd_vel.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_keyboard_cmd_vel)
install(PROGRAMS scripts/lite3_operator_dashboard.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_operator_dashboard)
install(PROGRAMS scripts/lite3_log_analyzer.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_log_analyzer)
install(PROGRAMS scripts/lite3_offline_preflight.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_offline_preflight)
install(PROGRAMS scripts/lite3_bag_recorder.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_bag_recorder)
install(PROGRAMS tools/lite3_ros_chain_test.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_ros_chain_test)
install(PROGRAMS tools/run_icp_bag_experiment.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME run_icp_bag_experiment)
install(PROGRAMS scripts/d455_center_depth_probe.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME d455_center_depth_probe)
install(TARGETS lite3_telemetry_bridge DESTINATION lib/${PROJECT_NAME})
install(FILES "${LITE3_SDK_LIB}" DESTINATION lib)

ament_package()
