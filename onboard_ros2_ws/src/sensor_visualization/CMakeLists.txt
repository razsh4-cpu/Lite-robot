cmake_minimum_required(VERSION 3.8)
project(sensor_visualization)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(lite3_control_safety test/test_lite3_control_safety.py)
  ament_add_pytest_test(xbox_remote_deadman test/test_xbox_remote_deadman.py)
  ament_add_pytest_test(onboard_startup test/test_onboard_startup.py)
  ament_add_pytest_test(xbox_reconnect_supervisor
    test/test_xbox_reconnect_supervisor.py)
  ament_add_pytest_test(autonomy_command_source
    test/test_autonomy_command_source.py)
  ament_add_pytest_test(laptop_xbox_c2
    test/test_laptop_xbox_c2.py)
  ament_add_pytest_test(day2_nav2_static
    test/test_day2_nav2_static.py)
  ament_add_pytest_test(nav_test_override
    test/test_nav_test_override.py)
  ament_add_pytest_test(localization_startup_supervisor
    test/test_localization_startup_supervisor.py)
  ament_add_pytest_test(day3_mission_registry
    test/test_day3_mission_registry.py)
  ament_add_pytest_test(robot_posture_cli
    test/test_robot_posture_cli.py)
  ament_add_pytest_test(platform_status_exporter
    test/test_platform_status_exporter.py)
endif()

set(LITE3_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../Lite3_MotionSDK" CACHE PATH
  "Path to the vendor Lite3 MotionSDK")
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
install(PROGRAMS scripts/lite3_xbox_device_valid.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_xbox_device_valid)
install(PROGRAMS scripts/lite3_xbox_startup.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_xbox_startup)
install(PROGRAMS scripts/lite3_xbox_reconnect_supervisor.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_xbox_reconnect_supervisor)
install(PROGRAMS scripts/lite3_xbox_diagnose.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_xbox_diagnose)
install(PROGRAMS scripts/lite3_high_level_xbox_runtime.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_high_level_xbox_runtime)
install(PROGRAMS scripts/lite3_high_level_runtime.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_high_level_runtime)
install(PROGRAMS scripts/lite3_autonomy_command_source.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_autonomy_command_source)
install(PROGRAMS scripts/lite3_laptop_xbox_source.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_laptop_xbox_source)
install(PROGRAMS scripts/lite3_posture_guard.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_posture_guard)
install(PROGRAMS scripts/lite3_system_health.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_system_health)
install(PROGRAMS scripts/lite3_headless_admin.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3-headless)
install(PROGRAMS scripts/lite3_readiness_status.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_readiness_status)
install(PROGRAMS scripts/lite3_localization_start.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_localization_start)
install(PROGRAMS scripts/lite3_localization_supervisor.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_localization_supervisor)
install(PROGRAMS scripts/lite3_localization_lifecycle_ready.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_localization_lifecycle_ready)
install(PROGRAMS scripts/lite3_map_manager.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_map_manager)
install(PROGRAMS scripts/lite3_ros_network_ready.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_ros_network_ready)
install(PROGRAMS scripts/lite3_ros_inputs_ready.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_ros_inputs_ready)
install(PROGRAMS scripts/lite3_nav2_preflight.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_nav2_preflight)
install(PROGRAMS scripts/lite3_nav_test_override.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_nav_test_override)
install(FILES scripts/lite3_nav_test_override.py
  DESTINATION lib/${PROJECT_NAME})
install(PROGRAMS scripts/lite3_release_autonomy.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_release_autonomy)
install(PROGRAMS scripts/lite3_nav2_safety_monitor.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_nav2_safety_monitor)
install(PROGRAMS scripts/lite3_relocalization_motion.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_relocalization_motion)
install(PROGRAMS scripts/lite3_relocalization_run.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_relocalization_run)
install(PROGRAMS scripts/lite3_localization_gate.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_localization_gate)
install(PROGRAMS scripts/lite3_high_level_ros_watchdog.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_high_level_ros_watchdog)
install(PROGRAMS scripts/lite3_mission_manager.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_mission_manager)
install(PROGRAMS scripts/lite3_platform_status_exporter.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lite3_platform_status_exporter)
install(TARGETS lite3_telemetry_bridge DESTINATION lib/${PROJECT_NAME})
install(FILES "${LITE3_SDK_LIB}" DESTINATION lib)

ament_package()
