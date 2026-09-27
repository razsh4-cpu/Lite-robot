import math


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class PlanarStartupOrigin:
    """Express an absolute planar vendor pose relative to the first sample."""

    def __init__(self):
        self.origin = None

    def transform(self, x, y, yaw):
        values = tuple(float(v) for v in (x, y, yaw))
        if not all(math.isfinite(v) for v in values):
            raise ValueError("non-finite planar odometry pose")
        first = self.origin is None
        if first:
            self.origin = values
        x0, y0, yaw0 = self.origin
        dx, dy = values[0] - x0, values[1] - y0
        cosine, sine = math.cos(yaw0), math.sin(yaw0)
        return (
            cosine * dx + sine * dy,
            -sine * dx + cosine * dy,
            wrap_angle(values[2] - yaw0),
            first,
        )

JOINT_NAMES = (
    "LF_Joint", "LF_Joint_1", "LF_Joint_2",
    "RF_Joint", "RF_Joint_1", "RF_Joint_2",
    "LB_Joint", "LB_Joint_1", "LB_Joint_2",
    "RB_Joint", "RB_Joint_1", "RB_Joint_2",
)


def feedback_is_fresh(last_received, now, timeout):
    return (last_received is not None and timeout > 0.0 and
            0.0 <= now - last_received <= timeout)


def quaternion_from_rpy(roll, pitch, yaw):
    cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def decode_robot_state(state):
    rpy_rad = tuple(math.radians(float(v)) for v in state.rpy)
    values = (
        *rpy_rad,
        *(float(v) for v in state.rpy_vel),
        *(float(v) for v in state.xyz_acc),
        *(float(v) for v in state.pos_world),
        *(float(v) for v in state.vel_world),
        *(float(v) for v in state.vel_body),
        float(state.battery_level),
    )
    if not all(math.isfinite(v) for v in values):
        raise ValueError("non-finite Lite3 RobotState")
    return {
        "basic_state": int(state.robot_basic_state),
        "battery": float(state.battery_level),
        "rpy": rpy_rad,
        "orientation": quaternion_from_rpy(*rpy_rad),
        "angular_velocity": tuple(float(v) for v in state.rpy_vel),
        "linear_acceleration": tuple(float(v) for v in state.xyz_acc),
        "position_xy": (float(state.pos_world[0]), float(state.pos_world[1])),
        "velocity_world": tuple(float(v) for v in state.vel_world),
        "velocity_body": tuple(float(v) for v in state.vel_body),
    }


def decode_joint_state(state):
    # The high-level transfer protocol reports only joint angles. Its sign is
    # opposite the vendor URDF/ROS convention, as documented by the plugin.
    positions = tuple(-float(getattr(state, name)) for name in JOINT_NAMES)
    if not all(math.isfinite(v) for v in positions):
        raise ValueError("non-finite Lite3 JointState")
    return positions
