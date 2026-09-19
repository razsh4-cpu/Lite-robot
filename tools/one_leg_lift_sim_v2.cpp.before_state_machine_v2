#include "tools/lite3_leg_kinematics.hpp"

#include <mujoco/mujoco.h>

#include <Eigen/Core>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <deque>
#include <sstream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using lite3::Leg;
constexpr int kJointCount = 12;
constexpr double kPi = 3.14159265358979323846;
constexpr double kTimeStep = 0.001;
constexpr double kLogPeriod = 0.01;
// The research parameters retain this vendor-documented PD pair as a commented
// alternative to 100/2.5. The stiffer setting avoids centimetre-scale virtual
// spring sag in the contact model. It remains position control; tau_ff is zero.
constexpr double kStanceKp = 180.0;
constexpr double kStanceKd = 3.5;
constexpr double kSwingKp = 180.0;
constexpr double kSwingKd = 3.5;
constexpr double kTorqueLimitNm = 30.0;
// Includes compliance compensation. The acceptance criterion is 5-10 mm of
// measured world-frame clearance, not the unloaded kinematic target alone.
constexpr double kLiftM = 0.015;
constexpr double kBodyHeightCompensationM = 0.006;
constexpr double kAttitudeCorrectionMetersPerRad = 0.15;
constexpr double kMaximumAttitudeCorrectionM = 0.008;
constexpr double kSimulationContactThresholdN = 2.0;
constexpr double kAbortAngleRad = 12.0 * kPi / 180.0;
constexpr double kMinimumBodyHeightM = 0.22;
constexpr double kMaximumBodyHeightM = 0.40;

enum class State {
  STAND_INITIAL,
  SHIFT_WEIGHT,
  LIFT_LEG,
  HOLD_LEG,
  MOVE_LEG_FORWARD,
  RETURN_LEG,
  LOWER_LEG,
  VERIFY_CONTACT,
  STAND_FINAL,
  COMPLETE,
};

struct StateSpec {
  State state;
  double duration_s;
};

constexpr std::array<StateSpec, 9> kSequence{{
    {State::STAND_INITIAL, 2.0},
    {State::SHIFT_WEIGHT, 2.0},
    {State::LIFT_LEG, 1.5},
    {State::HOLD_LEG, 1.0},
    {State::MOVE_LEG_FORWARD, 1.0},
    {State::RETURN_LEG, 1.0},
    {State::LOWER_LEG, 1.5},
    {State::VERIFY_CONTACT, 0.75},
    {State::STAND_FINAL, 2.0},
}};

const char* StateName(State state) {
  switch (state) {
    case State::STAND_INITIAL: return "STAND";
    case State::SHIFT_WEIGHT: return "SHIFT_WEIGHT";
    case State::LIFT_LEG: return "LIFT_LEG";
    case State::HOLD_LEG: return "HOLD_LEG";
    case State::MOVE_LEG_FORWARD: return "MOVE_LEG_FORWARD";
    case State::RETURN_LEG: return "RETURN_LEG";
    case State::LOWER_LEG: return "LOWER_LEG";
    case State::VERIFY_CONTACT: return "VERIFY_CONTACT";
    case State::STAND_FINAL: return "STAND";
    case State::COMPLETE: return "COMPLETE";
  }
  return "UNKNOWN";
}

bool IsLiftInterval(State state) {
  return state == State::LIFT_LEG || state == State::HOLD_LEG ||
         state == State::MOVE_LEG_FORWARD || state == State::RETURN_LEG ||
         state == State::LOWER_LEG;
}

struct Options {
  std::filesystem::path model_path =
      "third_party/deep_robotics_model/Lite3/Lite3_mjcf/mjcf/Lite3.xml";
  std::filesystem::path output_dir = "artifacts/one_leg_lift";

  double forward_m = 0.0;

  // Simulation-only runtime parameters. Defaults preserve the validated
  // deterministic baseline.
  double shift_x_m = 0.060;
  double shift_y_m = 0.060;
  double shift_s = 2.0;
  double hold_s = 0.0;
  double lift_m = 0.015;
  double lift_s = 1.5;
  double lower_s = 1.5;
  double kp = 180.0;
  double kd = 3.5;

  // Monte Carlo model/controller perturbations.
  double payload_kg = 0.0;
  double com_offset_x_m = 0.0;
  double com_offset_y_m = 0.0;
  double friction_scale = 1.0;
  double compliance_scale = 1.0;
  double joint_offset_rad = 0.0;
  double sensor_noise_rad = 0.0;
  double delay_s = 0.0;
  unsigned int seed = 1;
};

Options ParseOptions(int argc, char** argv) {
  Options options;
  for (int i = 1; i < argc; ++i) {
    const std::string argument = argv[i];
    if (argument == "--model" && i + 1 < argc) {
      options.model_path = argv[++i];
    } else if (argument == "--output-dir" && i + 1 < argc) {
      options.output_dir = argv[++i];
    } else if (argument == "--forward-mm" && i + 1 < argc) {
      options.forward_m = std::stod(argv[++i]) / 1000.0;
      if (options.forward_m < 0.0 || options.forward_m > 0.010) {
        throw std::runtime_error("--forward-mm must be between 0 and 10");
      }
    } else if (argument == "--shift-x-mm" && i + 1 < argc) {
      options.shift_x_m = std::stod(argv[++i]) / 1000.0;
    } else if (argument == "--shift-y-mm" && i + 1 < argc) {
      options.shift_y_m = std::stod(argv[++i]) / 1000.0;
    } else if (argument == "--shift-s" && i + 1 < argc) {
      options.shift_s = std::stod(argv[++i]);
    } else if (argument == "--hold-s" && i + 1 < argc) {
      options.hold_s = std::stod(argv[++i]);
    } else if (argument == "--lift-mm" && i + 1 < argc) {
      options.lift_m = std::stod(argv[++i]) / 1000.0;
    } else if (argument == "--lift-s" && i + 1 < argc) {
      options.lift_s = std::stod(argv[++i]);
    } else if (argument == "--lower-s" && i + 1 < argc) {
      options.lower_s = std::stod(argv[++i]);
    } else if (argument == "--kp" && i + 1 < argc) {
      options.kp = std::stod(argv[++i]);
    } else if (argument == "--kd" && i + 1 < argc) {
      options.kd = std::stod(argv[++i]);
    } else if (argument == "--payload-kg" && i + 1 < argc) {
      options.payload_kg = std::stod(argv[++i]);
    } else if (argument == "--com-offset-x-mm" && i + 1 < argc) {
      options.com_offset_x_m = std::stod(argv[++i]) / 1000.0;
    } else if (argument == "--com-offset-y-mm" && i + 1 < argc) {
      options.com_offset_y_m = std::stod(argv[++i]) / 1000.0;
    } else if (argument == "--friction-scale" && i + 1 < argc) {
      options.friction_scale = std::stod(argv[++i]);
    } else if (argument == "--compliance-scale" && i + 1 < argc) {
      options.compliance_scale = std::stod(argv[++i]);
    } else if (argument == "--joint-offset-rad" && i + 1 < argc) {
      options.joint_offset_rad = std::stod(argv[++i]);
    } else if (argument == "--sensor-noise-rad" && i + 1 < argc) {
      options.sensor_noise_rad = std::stod(argv[++i]);
    } else if (argument == "--delay-ms" && i + 1 < argc) {
      options.delay_s = std::stod(argv[++i]) / 1000.0;
    } else if (argument == "--seed" && i + 1 < argc) {
      options.seed = static_cast<unsigned int>(std::stoul(argv[++i]));
    } else {
      throw std::runtime_error("unknown or incomplete argument: " + argument);
    }
  }
  return options;
}

Eigen::Vector3d StandingAngles() {
  constexpr double thigh = 0.20;
  constexpr double shank = 0.21;  // The controller parameter, intentionally.
  constexpr double height = 0.30;
  const double hip = -std::acos((thigh * thigh + height * height - shank * shank) /
                                (2.0 * thigh * height));
  const double knee = kPi - std::acos((thigh * thigh + shank * shank - height * height) /
                                      (2.0 * thigh * shank));
  return {0.0, hip, knee};
}

double RuntimeDuration(const StateSpec& spec, const Options& options) {
  switch (spec.state) {
    case State::SHIFT_WEIGHT: return options.shift_s + options.hold_s;
    case State::LIFT_LEG: return options.lift_s;
    case State::LOWER_LEG: return options.lower_s;
    default: return spec.duration_s;
  }
}

double StateStartTime(std::size_t state_index, const Options& options) {
  double start = 0.0;
  for (std::size_t i = 0; i < state_index; ++i)
    start += RuntimeDuration(kSequence[i], options);
  return start;
}

std::size_t StateIndexAt(double time_s, const Options& options) {
  double end = 0.0;
  for (std::size_t i = 0; i < kSequence.size(); ++i) {
    end += RuntimeDuration(kSequence[i], options);
    if (time_s < end) return i;
  }
  return kSequence.size();
}

std::array<Eigen::Vector3d, 4> DesiredFeet(
    State state, double phase, const Options& options,
    const std::array<Eigen::Vector3d, 4>& nominal) {
  const Eigen::Vector3d body_shift_world(
      -options.shift_x_m, options.shift_y_m, 0.0);
  const Eigen::Vector3d shifted_foot_relative_body = -body_shift_world;
  const double smooth = lite3::Quintic(phase);
  double shift_scale = 1.0;
  double lift_scale = 0.0;
  double forward_scale = 0.0;

  switch (state) {
    case State::STAND_INITIAL:
      shift_scale = 0.0;
      break;
    case State::SHIFT_WEIGHT:
      shift_scale = smooth;
      break;
    case State::LIFT_LEG:
      lift_scale = smooth;
      break;
    case State::HOLD_LEG:
      lift_scale = 1.0;
      break;
    case State::MOVE_LEG_FORWARD:
      lift_scale = 1.0;
      forward_scale = smooth;
      break;
    case State::RETURN_LEG:
      lift_scale = 1.0;
      forward_scale = 1.0 - smooth;
      break;
    case State::LOWER_LEG:
      lift_scale = 1.0 - smooth;
      break;
    case State::VERIFY_CONTACT:
      break;
    case State::STAND_FINAL:
      shift_scale = 1.0 - smooth;
      break;
    case State::COMPLETE:
      shift_scale = 0.0;
      break;
  }

  std::array<Eigen::Vector3d, 4> targets = nominal;
  for (Eigen::Vector3d& target : targets) {
    target += shift_scale * shifted_foot_relative_body;
    // Coordinated extension of the stance geometry compensates the measured
    // PD spring sag while weight moves onto three legs.
    target.z() -= shift_scale * kBodyHeightCompensationM;
  }
  Eigen::Vector3d& fr = targets[lite3::LegIndex(Leg::FR)];
  fr.z() += lift_scale * options.lift_m;
  fr.x() += forward_scale * options.forward_m;
  return targets;
}

std::array<double, 3> QuaternionToRpy(const mjtNum* quaternion) {
  const double w = quaternion[0];
  const double x = quaternion[1];
  const double y = quaternion[2];
  const double z = quaternion[3];
  const double roll = std::atan2(2.0 * (w * x + y * z),
                                 1.0 - 2.0 * (x * x + y * y));
  const double pitch_argument = std::clamp(2.0 * (w * y - z * x), -1.0, 1.0);
  const double pitch = std::asin(pitch_argument);
  const double yaw = std::atan2(2.0 * (w * z + x * y),
                                1.0 - 2.0 * (y * y + z * z));
  return {roll, pitch, yaw};
}

double SignedTriangleMargin(const std::array<Eigen::Vector2d, 3>& triangle,
                            const Eigen::Vector2d& point) {
  double area_twice = 0.0;
  for (int i = 0; i < 3; ++i) {
    const Eigen::Vector2d& a = triangle[i];
    const Eigen::Vector2d& b = triangle[(i + 1) % 3];
    area_twice += a.x() * b.y() - a.y() * b.x();
  }
  const double orientation = area_twice >= 0.0 ? 1.0 : -1.0;
  double margin = std::numeric_limits<double>::infinity();
  for (int i = 0; i < 3; ++i) {
    const Eigen::Vector2d edge = triangle[(i + 1) % 3] - triangle[i];
    const Eigen::Vector2d offset = point - triangle[i];
    const double cross = edge.x() * offset.y() - edge.y() * offset.x();
    margin = std::min(margin, orientation * cross / edge.norm());
  }
  return margin;
}

int LegForGeom(const mjModel* model, int geom_id) {
  if (geom_id < 0) return -1;
  const char* name = mj_id2name(model, mjOBJ_GEOM, geom_id);
  if (!name) return -1;
  for (int leg = 0; leg < 4; ++leg) {
    const std::string prefix = std::string(lite3::kLegNames[leg]) + "_";
    if (std::string(name).rfind(prefix, 0) == 0) return leg;
  }
  return -1;
}

// The vendor MJCF models each distal leg with both a shank mesh and a foot
// sphere. Aggregate ground reaction contacts from either geometry and retain
// the exact geometry names in the report so this proxy remains auditable.
std::array<double, 4> LegGroundForces(const mjModel* model, const mjData* data,
                                      std::set<std::string>* contact_geometries) {
  std::array<double, 4> forces{};
  for (int contact_index = 0; contact_index < data->ncon; ++contact_index) {
    const mjContact& contact = data->contact[contact_index];
    int leg_index = LegForGeom(model, contact.geom1);
    const int second_leg = LegForGeom(model, contact.geom2);
    if (leg_index < 0) leg_index = second_leg;
    if (leg_index < 0) continue;
    if (contact_geometries) {
      const int robot_geom = LegForGeom(model, contact.geom1) >= 0
                                 ? contact.geom1 : contact.geom2;
      const char* name = mj_id2name(model, mjOBJ_GEOM, robot_geom);
      if (name) contact_geometries->insert(name);
    }
    mjtNum wrench[6]{};
    mj_contactForce(model, data, contact_index, wrench);
    forces[leg_index] += std::abs(static_cast<double>(wrench[0]));
  }
  return forces;
}

std::string JsonNumber(double value) {
  if (!std::isfinite(value)) return "null";
  std::ostringstream stream;
  stream << std::setprecision(10) << value;
  return stream.str();
}

struct Metrics {
  bool aborted = false;
  std::string abort_reason;
  double max_abs_roll_rad = 0.0;
  double max_abs_pitch_rad = 0.0;
  double max_abs_roll_lift_rad = 0.0;
  double max_abs_pitch_lift_rad = 0.0;
  double min_support_margin_lift_m = std::numeric_limits<double>::infinity();
  double max_fr_lift_m = 0.0;
  double min_body_height_m = std::numeric_limits<double>::infinity();
  double max_body_height_m = -std::numeric_limits<double>::infinity();
  double max_ik_residual_m = 0.0;
  double max_fk_model_error_m = 0.0;
  double peak_commanded_torque_nm = 0.0;
  double max_tracking_error_rad = 0.0;
  double max_joint_rate_rad_s = 0.0;
  double touchdown_velocity_m_s = 0.0;
  double final_joint_error_rad = 0.0;
  std::array<double, 4> min_force_lift{{
      std::numeric_limits<double>::infinity(),
      std::numeric_limits<double>::infinity(),
      std::numeric_limits<double>::infinity(),
      std::numeric_limits<double>::infinity()}};
  std::array<double, 4> max_force_lift{};
  std::array<double, 4> sum_force_lift{};
  int force_lift_samples = 0;
  int fr_unloaded_samples = 0;
  int stance_all_loaded_samples = 0;
  int hold_samples = 0;
  int hold_fr_unloaded_samples = 0;
  int final_contact_samples = 0;
  int final_all_contact_samples = 0;
  std::set<std::string> contacted_leg_geometries;
};

}  // namespace

int main(int argc, char** argv) {
  try {
    const Options options = ParseOptions(argc, argv);
    std::filesystem::create_directories(options.output_dir);
    const std::filesystem::path csv_path = options.output_dir / "trace.csv";
    const std::filesystem::path json_path = options.output_dir / "summary.json";

    char load_error[2048]{};
    mjModel* model = mj_loadXML(options.model_path.c_str(), nullptr, load_error,
                                sizeof(load_error));
    if (!model) throw std::runtime_error(std::string("MJCF load failed: ") + load_error);
    mjData* data = mj_makeData(model);
    if (!data) {
      mj_deleteModel(model);
      throw std::runtime_error("mj_makeData failed");
    }
    if (model->nq != 19 || model->nv != 18 || model->nu != kJointCount) {
      throw std::runtime_error("unexpected Lite3 model dimensions");
    }
    model->opt.timestep = kTimeStep;
    // shank.STL extends 0.50 mm below the dedicated foot sphere and otherwise
    // masks small foot lifts with duplicate ground contacts. Keep the source
    // MJCF unchanged, but use its explicit foot spheres as the sole ground
    // contact representation for this foot-control experiment.
    for (int geom = 0; geom < model->ngeom; ++geom) {
      const char* name = mj_id2name(model, mjOBJ_GEOM, geom);
      if (name && std::string(name).find("_SHANK_collision") != std::string::npos) {
        model->geom_contype[geom] = 0;
        model->geom_conaffinity[geom] = 0;
      }
    }

    const Eigen::Vector3d standing = StandingAngles();
    std::array<Eigen::Vector3d, 4> nominal_feet;
    for (int leg = 0; leg < 4; ++leg) {
      nominal_feet[leg] = lite3::FootPositionBody(static_cast<Leg>(leg), standing);
    }

    const double foot_radius_m = 0.022;
    data->qpos[0] = 0.0;
    data->qpos[1] = 0.0;
    data->qpos[2] = foot_radius_m - nominal_feet[0].z();
    data->qpos[3] = 1.0;
    data->qpos[4] = data->qpos[5] = data->qpos[6] = 0.0;
    for (int leg = 0; leg < 4; ++leg) {
      for (int joint = 0; joint < 3; ++joint) {
        data->qpos[7 + 3 * leg + joint] = standing[joint];
      }
    }
    mju_zero(data->qvel, model->nv);
    mj_forward(model, data);

    std::array<int, 4> foot_body_ids{};
    std::array<int, 4> foot_geom_ids{};
    for (int leg = 0; leg < 4; ++leg) {
      const std::string prefix = lite3::kLegNames[leg];
      foot_body_ids[leg] = mj_name2id(model, mjOBJ_BODY, (prefix + "_FOOT").c_str());
      foot_geom_ids[leg] = mj_name2id(model, mjOBJ_GEOM,
                                     (prefix + "_FOOT_collision").c_str());
      if (foot_body_ids[leg] < 0 || foot_geom_ids[leg] < 0) {
        throw std::runtime_error("foot body/geometry lookup failed for " + prefix);
      }
    }
    const int torso_body_id = mj_name2id(model, mjOBJ_BODY, "TORSO");
    if (torso_body_id < 0) throw std::runtime_error("TORSO body lookup failed");

    if (options.payload_kg < 0.0)
      throw std::runtime_error("--payload-kg must be >= 0");
    if (options.friction_scale <= 0.0)
      throw std::runtime_error("--friction-scale must be > 0");
    if (options.compliance_scale <= 0.0)
      throw std::runtime_error("--compliance-scale must be > 0");
    if (options.shift_s <= 0.0 || options.lift_s <= 0.0 ||
        options.lower_s <= 0.0 || options.hold_s < 0.0)
      throw std::runtime_error("trajectory durations must be positive");
    if (options.kp <= 0.0 || options.kd < 0.0)
      throw std::runtime_error("invalid PD gains");

    // Simulation-only payload approximation: additional rigid mass attached
    // to the torso. The inertia is intentionally left unchanged, so this is
    // a conservative translational-load perturbation rather than a fabricated
    // payload geometry.
    model->body_mass[torso_body_id] += options.payload_kg;

    // Perturb the torso inertial COM in its local body frame.
    model->body_ipos[3 * torso_body_id + 0] += options.com_offset_x_m;
    model->body_ipos[3 * torso_body_id + 1] += options.com_offset_y_m;

    // Scale the three MuJoCo friction coefficients on the four explicit feet.
    for (int leg = 0; leg < 4; ++leg) {
      const int geom = foot_geom_ids[leg];
      for (int j = 0; j < 3; ++j)
        model->geom_friction[3 * geom + j] *= options.friction_scale;

      // MuJoCo solref[0] is the contact time constant in the standard
      // positive format. Larger values produce a softer/slower contact.
      if (model->geom_solref[2 * geom] > 0.0)
        model->geom_solref[2 * geom] *= options.compliance_scale;
    }

    std::mt19937 rng(options.seed);
    std::normal_distribution<double> sensor_noise(
        0.0, std::max(0.0, options.sensor_noise_rad));

    // Fixed per-run joint-zero perturbation. Same requested magnitude is
    // sampled independently for each joint.
    std::uniform_real_distribution<double> joint_offset_dist(
        -std::abs(options.joint_offset_rad),
         std::abs(options.joint_offset_rad));
    std::array<double, kJointCount> joint_offsets{};
    for (double& offset : joint_offsets)
      offset = joint_offset_dist(rng);

    struct DelayedObservation {
      double time = 0.0;
      std::array<double, kJointCount> q{};
      std::array<double, kJointCount> dq{};
    };
    std::deque<DelayedObservation> observation_history;

    Metrics metrics;
    for (int leg = 0; leg < 4; ++leg) {
      Eigen::Vector3d model_foot;
      for (int xyz = 0; xyz < 3; ++xyz) {
        model_foot[xyz] = data->xpos[3 * foot_body_ids[leg] + xyz] -
                          data->xpos[3 * torso_body_id + xyz];
      }
      metrics.max_fk_model_error_m = std::max(
          metrics.max_fk_model_error_m, (model_foot - nominal_feet[leg]).norm());
    }
    if (metrics.max_fk_model_error_m > 1e-8) {
      throw std::runtime_error("implemented FK does not match the loaded MJCF");
    }

    std::ofstream csv(csv_path);
    if (!csv) throw std::runtime_error("cannot open trace CSV");
    csv << "time_s,state,roll_rad,pitch_rad,yaw_rad,body_x_m,body_y_m,body_z_m,"
           "com_x_m,com_y_m,support_margin_m,fr_foot_z_m,fr_lift_m,"
           "fl_force_n,fr_force_n,hl_force_n,hr_force_n,"
           "fr_q0,fr_q1,fr_q2,fr_qd0,fr_qd1,fr_qd2,max_abs_tau_nm,ik_residual_m\n";

    std::array<Eigen::Vector3d, 4> ik_seed{{standing, standing, standing, standing}};
    std::array<Eigen::Vector3d, 4> commanded_q = ik_seed;
    const double total_time_s = StateStartTime(kSequence.size(), options);
    double next_log_time_s = 0.0;
    double initial_fr_foot_world_z = 0.0;
    bool initial_fr_height_set = false;
    double previous_fr_world_z = 0.0;
    double previous_fr_time = 0.0;
    bool previous_fr_set = false;
    bool touchdown_recorded = false;

    while (data->time < total_time_s && !metrics.aborted) {
      const std::size_t state_index = StateIndexAt(data->time, options);
      if (state_index >= kSequence.size()) break;
      const StateSpec& spec = kSequence[state_index];
      const double runtime_duration = RuntimeDuration(spec, options);
      double phase = (data->time - StateStartTime(state_index, options)) /
                     std::max(runtime_duration, 1e-9);

      // SHIFT_WEIGHT can include a shifted hold after the quintic shift.
      if (spec.state == State::SHIFT_WEIGHT && options.hold_s > 0.0) {
        phase = std::min(
            1.0,
            (data->time - StateStartTime(state_index, options)) /
                std::max(options.shift_s, 1e-9));
      }

      auto desired_feet = DesiredFeet(spec.state, phase, options, nominal_feet);
      const auto command_rpy = QuaternionToRpy(data->qpos + 3);
      if (spec.state != State::STAND_INITIAL && spec.state != State::COMPLETE) {
        for (int leg = 0; leg < 4; ++leg) {
          const double side_sign = lite3::IsLeft(static_cast<Leg>(leg)) ? 1.0 : -1.0;
          const double front_sign = lite3::IsFront(static_cast<Leg>(leg)) ? 1.0 : -1.0;
          const double correction = std::clamp(
              kAttitudeCorrectionMetersPerRad *
                  (command_rpy[0] * side_sign - command_rpy[1] * front_sign),
              -kMaximumAttitudeCorrectionM, kMaximumAttitudeCorrectionM);
          desired_feet[leg].z() += correction;
        }
      }
      double step_max_ik_residual = 0.0;
      for (int leg = 0; leg < 4; ++leg) {
        const auto ik = lite3::SolveFootIk(static_cast<Leg>(leg), desired_feet[leg],
                                           ik_seed[leg]);
        step_max_ik_residual = std::max(step_max_ik_residual, ik.residual_m);
        if (!ik.converged) {
          metrics.aborted = true;
          metrics.abort_reason = "IK failed for " + std::string(lite3::kLegNames[leg]);
          break;
        }
        commanded_q[leg] = ik.q;
        ik_seed[leg] = ik.q;
      }
      metrics.max_ik_residual_m = std::max(metrics.max_ik_residual_m,
                                           step_max_ik_residual);
      if (metrics.aborted) break;

      DelayedObservation observation;
      observation.time = data->time;
      for (int joint = 0; joint < kJointCount; ++joint) {
        observation.q[joint] = data->qpos[7 + joint];
        observation.dq[joint] = data->qvel[6 + joint];
      }
      observation_history.push_back(observation);

      const double desired_observation_time = data->time - options.delay_s;
      while (observation_history.size() > 1 &&
             observation_history[1].time <= desired_observation_time) {
        observation_history.pop_front();
      }
      const DelayedObservation& delayed = observation_history.front();

      double max_abs_tau = 0.0;
      for (int joint = 0; joint < kJointCount; ++joint) {
        const int leg = joint / 3;
        const int within_leg = joint % 3;
        const double true_q = data->qpos[7 + joint];
        const double true_dq = data->qvel[6 + joint];

        const double measured_q =
            delayed.q[joint] + joint_offsets[joint] + sensor_noise(rng);
        const double measured_dq = delayed.dq[joint];

        const double desired = commanded_q[leg][within_leg];

        const double tracking_error = std::abs(desired - true_q);
        metrics.max_tracking_error_rad =
            std::max(metrics.max_tracking_error_rad, tracking_error);
        metrics.max_joint_rate_rad_s =
            std::max(metrics.max_joint_rate_rad_s, std::abs(true_dq));

        const double kp = options.kp;
        const double kd = options.kd;
        const double torque = std::clamp(
            kp * (desired - measured_q) - kd * measured_dq,
            -kTorqueLimitNm, kTorqueLimitNm);
        data->ctrl[joint] = torque;
        max_abs_tau = std::max(max_abs_tau, std::abs(torque));
      }
      metrics.peak_commanded_torque_nm = std::max(metrics.peak_commanded_torque_nm,
                                                   max_abs_tau);
      mj_step(model, data);

      const auto rpy = QuaternionToRpy(data->qpos + 3);
      metrics.max_abs_roll_rad = std::max(metrics.max_abs_roll_rad, std::abs(rpy[0]));
      metrics.max_abs_pitch_rad = std::max(metrics.max_abs_pitch_rad, std::abs(rpy[1]));
      metrics.min_body_height_m = std::min(metrics.min_body_height_m,
                                           static_cast<double>(data->qpos[2]));
      metrics.max_body_height_m = std::max(metrics.max_body_height_m,
                                           static_cast<double>(data->qpos[2]));

      const auto forces = LegGroundForces(model, data, &metrics.contacted_leg_geometries);
      const double fr_world_z = data->xpos[3 * foot_body_ids[1] + 2];
      if (!initial_fr_height_set && data->time >= 1.5) {
        initial_fr_foot_world_z = fr_world_z;
        initial_fr_height_set = true;
      }
      const double fr_lift = initial_fr_height_set ? fr_world_z - initial_fr_foot_world_z : 0.0;
      metrics.max_fr_lift_m = std::max(metrics.max_fr_lift_m, fr_lift);

      double fr_vertical_velocity = 0.0;
      if (previous_fr_set && data->time > previous_fr_time) {
        fr_vertical_velocity =
            (fr_world_z - previous_fr_world_z) /
            (data->time - previous_fr_time);
      }

      if (!touchdown_recorded &&
          (spec.state == State::LOWER_LEG ||
           spec.state == State::VERIFY_CONTACT) &&
          forces[1] >= kSimulationContactThresholdN &&
          previous_fr_set) {
        metrics.touchdown_velocity_m_s = fr_vertical_velocity;
        touchdown_recorded = true;
      }

      previous_fr_world_z = fr_world_z;
      previous_fr_time = data->time;
      previous_fr_set = true;

      std::array<Eigen::Vector2d, 3> support_triangle;
      for (int xyz = 0; xyz < 2; ++xyz) {
        support_triangle[0][xyz] = data->xpos[3 * foot_body_ids[0] + xyz];  // FL
        support_triangle[1][xyz] = data->xpos[3 * foot_body_ids[2] + xyz];  // HL
        support_triangle[2][xyz] = data->xpos[3 * foot_body_ids[3] + xyz];  // HR
      }
      const Eigen::Vector2d com(data->subtree_com[3 * torso_body_id],
                                data->subtree_com[3 * torso_body_id + 1]);
      const double support_margin = SignedTriangleMargin(support_triangle, com);

      if (IsLiftInterval(spec.state)) {
        metrics.max_abs_roll_lift_rad = std::max(metrics.max_abs_roll_lift_rad,
                                                 std::abs(rpy[0]));
        metrics.max_abs_pitch_lift_rad = std::max(metrics.max_abs_pitch_lift_rad,
                                                  std::abs(rpy[1]));
        metrics.min_support_margin_lift_m = std::min(metrics.min_support_margin_lift_m,
                                                     support_margin);
        for (int leg = 0; leg < 4; ++leg) {
          metrics.min_force_lift[leg] = std::min(metrics.min_force_lift[leg], forces[leg]);
          metrics.max_force_lift[leg] = std::max(metrics.max_force_lift[leg], forces[leg]);
          metrics.sum_force_lift[leg] += forces[leg];
        }
        ++metrics.force_lift_samples;
        if (forces[1] < kSimulationContactThresholdN) ++metrics.fr_unloaded_samples;
        if (forces[0] >= kSimulationContactThresholdN &&
            forces[2] >= kSimulationContactThresholdN &&
            forces[3] >= kSimulationContactThresholdN) {
          ++metrics.stance_all_loaded_samples;
        }
      }
      if (spec.state == State::HOLD_LEG) {
        ++metrics.hold_samples;
        if (forces[1] < kSimulationContactThresholdN) ++metrics.hold_fr_unloaded_samples;
      }
      if (spec.state == State::STAND_FINAL) {
        for (int joint = 0; joint < kJointCount; ++joint) {
          const double entry = standing[joint % 3];
          metrics.final_joint_error_rad =
              std::max(metrics.final_joint_error_rad,
                       std::abs(data->qpos[7 + joint] - entry));
        }
      }

      if (spec.state == State::VERIFY_CONTACT || spec.state == State::STAND_FINAL) {
        ++metrics.final_contact_samples;
        if (std::all_of(forces.begin(), forces.end(), [](double force) {
              return force >= kSimulationContactThresholdN;
            })) {
          ++metrics.final_all_contact_samples;
        }
      }

      if (std::abs(rpy[0]) > kAbortAngleRad || std::abs(rpy[1]) > kAbortAngleRad) {
        metrics.aborted = true;
        metrics.abort_reason = "body roll/pitch exceeded 12 degrees";
      } else if (data->qpos[2] < kMinimumBodyHeightM ||
                 data->qpos[2] > kMaximumBodyHeightM) {
        metrics.aborted = true;
        metrics.abort_reason = "body height left the 0.22-0.40 m simulation envelope";
      } else if (IsLiftInterval(spec.state) && phase > 0.2 && support_margin < -0.010) {
        metrics.aborted = true;
        metrics.abort_reason = "COM projection left the three-foot support triangle by over 10 mm";
      }

      if (data->time + 1e-12 >= next_log_time_s) {
        csv << std::fixed << std::setprecision(8)
            << data->time << ',' << StateName(spec.state) << ','
            << rpy[0] << ',' << rpy[1] << ',' << rpy[2] << ','
            << data->qpos[0] << ',' << data->qpos[1] << ',' << data->qpos[2] << ','
            << com.x() << ',' << com.y() << ',' << support_margin << ','
            << fr_world_z << ',' << fr_lift << ','
            << forces[0] << ',' << forces[1] << ',' << forces[2] << ',' << forces[3] << ','
            << data->qpos[10] << ',' << data->qpos[11] << ',' << data->qpos[12] << ','
            << commanded_q[1][0] << ',' << commanded_q[1][1] << ',' << commanded_q[1][2] << ','
            << max_abs_tau << ',' << step_max_ik_residual << '\n';
        next_log_time_s += kLogPeriod;
      }
    }
    csv.close();

    const double radians_to_degrees = 180.0 / kPi;
    const auto ratio = [](int numerator, int denominator) {
      return denominator > 0 ? static_cast<double>(numerator) / denominator : 0.0;
    };
    if (!metrics.aborted && metrics.max_fr_lift_m < 0.005) {
      metrics.aborted = true;
      metrics.abort_reason = "measured FR clearance did not reach 5 mm";
    } else if (!metrics.aborted &&
               ratio(metrics.hold_fr_unloaded_samples, metrics.hold_samples) < 0.95) {
      metrics.aborted = true;
      metrics.abort_reason = "FR did not remain unloaded during the hold";
    } else if (!metrics.aborted && metrics.min_support_margin_lift_m <= 0.0) {
      metrics.aborted = true;
      metrics.abort_reason = "COM projection left the three-foot support triangle";
    } else if (!metrics.aborted &&
               ratio(metrics.stance_all_loaded_samples, metrics.force_lift_samples) < 0.95) {
      metrics.aborted = true;
      metrics.abort_reason = "one or more stance feet lost load during the lift";
    } else if (!metrics.aborted &&
               ratio(metrics.final_all_contact_samples, metrics.final_contact_samples) < 0.95) {
      metrics.aborted = true;
      metrics.abort_reason = "all four contacts were not restored after lowering";
    }
    std::ofstream json(json_path);
    if (!json) throw std::runtime_error("cannot open summary JSON");
    json << "{\n"
         << "  \"engine\": \"MuJoCo " << mj_versionString() << "\",\n"
         << "  \"model\": \"" << options.model_path.string() << "\",\n"
         << "  \"selected_leg\": \"FR\",\n"
         << "  \"control\": \"joint position/PD, zero feed-forward torque\",\n"
         << "  \"contact_normalization\": \"dedicated foot spheres only; overlapping shank-floor contacts disabled at runtime\",\n"
         << "  \"completed\": " << (!metrics.aborted ? "true" : "false") << ",\n"
         << "  \"abort_reason\": \"" << metrics.abort_reason << "\",\n"
         << "  \"standing_joint_rad\": [" << standing[0] << ", " << standing[1]
         << ", " << standing[2] << "],\n"
         << "  \"body_shift_m\": [-0.06, 0.06, 0.0],\n"
         << "  \"stance_pd\": {\"kp\": " << kStanceKp << ", \"kd\": " << kStanceKd << "},\n"
         << "  \"swing_pd\": {\"kp\": " << kSwingKp << ", \"kd\": " << kSwingKd << "},\n"
         << "  \"requested_lift_m\": " << kLiftM << ",\n"
         << "  \"body_height_compensation_m\": " << kBodyHeightCompensationM << ",\n"
         << "  \"attitude_correction_m_per_rad\": "
         << kAttitudeCorrectionMetersPerRad << ",\n"
         << "  \"requested_forward_m\": " << options.forward_m << ",\n"
         << "  \"max_measured_fr_lift_m\": " << JsonNumber(metrics.max_fr_lift_m) << ",\n"
         << "  \"max_abs_roll_deg\": " << JsonNumber(metrics.max_abs_roll_rad * radians_to_degrees) << ",\n"
         << "  \"max_abs_pitch_deg\": " << JsonNumber(metrics.max_abs_pitch_rad * radians_to_degrees) << ",\n"
         << "  \"max_abs_roll_during_lift_deg\": "
         << JsonNumber(metrics.max_abs_roll_lift_rad * radians_to_degrees) << ",\n"
         << "  \"max_abs_pitch_during_lift_deg\": "
         << JsonNumber(metrics.max_abs_pitch_lift_rad * radians_to_degrees) << ",\n"
         << "  \"minimum_support_margin_during_lift_m\": "
         << JsonNumber(metrics.min_support_margin_lift_m) << ",\n"
         << "  \"body_height_range_m\": [" << JsonNumber(metrics.min_body_height_m)
         << ", " << JsonNumber(metrics.max_body_height_m) << "],\n"
         << "  \"max_fk_model_error_m\": " << JsonNumber(metrics.max_fk_model_error_m) << ",\n"
         << "  \"max_ik_residual_m\": " << JsonNumber(metrics.max_ik_residual_m) << ",\n"
         << "  \"peak_pd_torque_nm\": " << JsonNumber(metrics.peak_commanded_torque_nm) << ",\n"
         << "  \"simulation_contact_threshold_n\": " << kSimulationContactThresholdN << ",\n"
         << "  \"fr_unloaded_fraction_during_hold\": "
         << JsonNumber(ratio(metrics.hold_fr_unloaded_samples, metrics.hold_samples)) << ",\n"
         << "  \"all_stance_feet_loaded_fraction_during_lift\": "
         << JsonNumber(ratio(metrics.stance_all_loaded_samples, metrics.force_lift_samples)) << ",\n"
         << "  \"all_four_feet_contact_fraction_after_lowering\": "
         << JsonNumber(ratio(metrics.final_all_contact_samples, metrics.final_contact_samples)) << ",\n"
         << "  \"lift_force_min_n\": [";
    for (int leg = 0; leg < 4; ++leg) {
      if (leg) json << ", ";
      json << JsonNumber(metrics.min_force_lift[leg]);
    }
    json << "],\n  \"lift_force_mean_n\": [";
    for (int leg = 0; leg < 4; ++leg) {
      if (leg) json << ", ";
      json << JsonNumber(metrics.force_lift_samples > 0
                             ? metrics.sum_force_lift[leg] / metrics.force_lift_samples
                             : 0.0);
    }
    json << "],\n  \"lift_force_max_n\": [";
    for (int leg = 0; leg < 4; ++leg) {
      if (leg) json << ", ";
      json << JsonNumber(metrics.max_force_lift[leg]);
    }
    json << "],\n"
         << "  \"seed\": " << options.seed << ",\n"
         << "  \"shift_x_m\": " << options.shift_x_m << ",\n"
         << "  \"shift_y_m\": " << options.shift_y_m << ",\n"
         << "  \"shift_s\": " << options.shift_s << ",\n"
         << "  \"shift_hold_s\": " << options.hold_s << ",\n"
         << "  \"lift_m\": " << options.lift_m << ",\n"
         << "  \"lift_s\": " << options.lift_s << ",\n"
         << "  \"lower_s\": " << options.lower_s << ",\n"
         << "  \"kp\": " << options.kp << ",\n"
         << "  \"kd\": " << options.kd << ",\n"
         << "  \"payload_kg\": " << options.payload_kg << ",\n"
         << "  \"com_offset_x_m\": " << options.com_offset_x_m << ",\n"
         << "  \"com_offset_y_m\": " << options.com_offset_y_m << ",\n"
         << "  \"friction_scale\": " << options.friction_scale << ",\n"
         << "  \"compliance_scale\": " << options.compliance_scale << ",\n"
         << "  \"joint_offset_rad\": " << options.joint_offset_rad << ",\n"
         << "  \"sensor_noise_rad\": " << options.sensor_noise_rad << ",\n"
         << "  \"delay_s\": " << options.delay_s << ",\n"
         << "  \"max_tracking_error_rad\": "
         << JsonNumber(metrics.max_tracking_error_rad) << ",\n"
         << "  \"max_joint_rate_rad_s\": "
         << JsonNumber(metrics.max_joint_rate_rad_s) << ",\n"
         << "  \"touchdown_velocity_m_s\": "
         << JsonNumber(metrics.touchdown_velocity_m_s) << ",\n"
         << "  \"final_joint_error_rad\": "
         << JsonNumber(metrics.final_joint_error_rad) << ",\n"
         << "  \"contacted_leg_geometries\": [";
    bool first_geometry = true;
    for (const std::string& geometry : metrics.contacted_leg_geometries) {
      if (!first_geometry) json << ", ";
      json << "\"" << geometry << "\"";
      first_geometry = false;
    }
    json << "]\n}\n";
    json.close();

    std::cout << "Simulation " << (metrics.aborted ? "ABORTED" : "completed")
              << "\nTrace: " << csv_path << "\nSummary: " << json_path << "\n";
    if (metrics.aborted) {
      std::cerr << "Abort reason: " << metrics.abort_reason << "\n";
    }

    mj_deleteData(data);
    mj_deleteModel(model);
    return metrics.aborted ? 2 : 0;
  } catch (const std::exception& error) {
    std::cerr << "one_leg_lift_sim: " << error.what() << "\n";
    return 1;
  }
}
