#include <array>
#include <cmath>
#include <memory>

#include "geometry_msgs/msg/vector3_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "receiver.h"

namespace {
constexpr double kDegToRad = M_PI / 180.0;
constexpr std::array<const char *, 12> kJointNames = {
  "fl_hip_x", "fl_hip_y", "fl_knee", "fr_hip_x", "fr_hip_y", "fr_knee",
  "hl_hip_x", "hl_hip_y", "hl_knee", "hr_hip_x", "hr_hip_y", "hr_knee"};
}

class Lite3TelemetryBridge : public rclcpp::Node {
 public:
  Lite3TelemetryBridge() : Node("lite3_telemetry_bridge") {
    imu_pub_ = create_publisher<sensor_msgs::msg::Imu>("/lite3/imu/data", 20);
    joints_pub_ = create_publisher<sensor_msgs::msg::JointState>("/lite3/joint_states", 20);
    contacts_pub_ = create_publisher<geometry_msgs::msg::Vector3Stamped>("/lite3/contact_force_z", 20);
    receiver_ = std::make_unique<Receiver>();
    receiver_->RegisterCallBack([this](int code) {
      if (code == 0x0906) { received_.store(true); }
    });
    receiver_->StartWork();
    timer_ = create_wall_timer(std::chrono::milliseconds(10),
      std::bind(&Lite3TelemetryBridge::publish, this));
    RCLCPP_INFO(get_logger(), "Read-only Lite3 telemetry bridge started; it never sends a UDP command.");
  }

 private:
  void publish() {
    if (!received_.exchange(false)) return;
    const RobotData data = receiver_->GetState();
    const auto stamp = now();

    sensor_msgs::msg::Imu imu;
    imu.header.stamp = stamp;
    imu.header.frame_id = "base_link";
    const double roll = data.imu.angle_roll * kDegToRad;
    const double pitch = data.imu.angle_pitch * kDegToRad;
    const double yaw = data.imu.angle_yaw * kDegToRad;
    const double cr = std::cos(roll * 0.5), sr = std::sin(roll * 0.5);
    const double cp = std::cos(pitch * 0.5), sp = std::sin(pitch * 0.5);
    const double cy = std::cos(yaw * 0.5), sy = std::sin(yaw * 0.5);
    imu.orientation.w = cr * cp * cy + sr * sp * sy;
    imu.orientation.x = sr * cp * cy - cr * sp * sy;
    imu.orientation.y = cr * sp * cy + sr * cp * sy;
    imu.orientation.z = cr * cp * sy - sr * sp * cy;
    imu.angular_velocity.x = data.imu.angular_velocity_roll * kDegToRad;
    imu.angular_velocity.y = data.imu.angular_velocity_pitch * kDegToRad;
    imu.angular_velocity.z = data.imu.angular_velocity_yaw * kDegToRad;
    imu.linear_acceleration.x = data.imu.acc_x;
    imu.linear_acceleration.y = data.imu.acc_y;
    imu.linear_acceleration.z = data.imu.acc_z;
    imu_pub_->publish(imu);

    sensor_msgs::msg::JointState joints;
    joints.header = imu.header;
    joints.name.assign(kJointNames.begin(), kJointNames.end());
    joints.position.resize(12); joints.velocity.resize(12); joints.effort.resize(12);
    for (size_t i = 0; i < 12; ++i) {
      joints.position[i] = data.joint_data.joint_data[i].position;
      joints.velocity[i] = data.joint_data.joint_data[i].velocity;
      joints.effort[i] = data.joint_data.joint_data[i].torque;
    }
    joints_pub_->publish(joints);

    geometry_msgs::msg::Vector3Stamped contacts;
    contacts.header = imu.header;
    contacts.vector.x = data.contact_force.fl_leg[2];
    contacts.vector.y = data.contact_force.fr_leg[2];
    contacts.vector.z = data.contact_force.hl_leg[2];
    contacts_pub_->publish(contacts);
  }

  std::unique_ptr<Receiver> receiver_;
  std::atomic_bool received_{false};
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr imu_pub_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joints_pub_;
  rclcpp::Publisher<geometry_msgs::msg::Vector3Stamped>::SharedPtr contacts_pub_;
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Lite3TelemetryBridge>());
  rclcpp::shutdown();
  return 0;
}
