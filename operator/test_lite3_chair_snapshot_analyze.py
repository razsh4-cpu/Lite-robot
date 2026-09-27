#!/usr/bin/env python3
"""Regression tests for dry-run path orientation analysis."""

import math

from lite3_chair_snapshot_analyze import path_tangent_yaw


def test_path_tangent_overrides_zero_navfn_orientation():
    poses = [
        {"x": 0.0, "y": 0.0, "yaw": 0.0},
        {"x": 0.0, "y": 0.5, "yaw": 0.0},
        {"x": 0.0, "y": 1.0, "yaw": 0.0},
    ]
    assert math.isclose(path_tangent_yaw(poses, 1, 0.0), math.pi / 2)


def test_path_tangent_handles_repeated_and_terminal_poses():
    poses = [
        {"x": 0.0, "y": 0.0, "yaw": 0.7},
        {"x": 0.0, "y": 0.0, "yaw": 0.0},
        {"x": -0.5, "y": 0.0, "yaw": 0.0},
    ]
    assert math.isclose(abs(path_tangent_yaw(poses, 1, 0.0)), math.pi)
    assert math.isclose(abs(path_tangent_yaw(poses, 2, 0.0)), math.pi)


def test_path_tangent_uses_fallback_for_single_pose():
    poses = [{"x": 1.0, "y": 2.0, "yaw": 0.4}]
    assert path_tangent_yaw(poses, 0, 0.4) == 0.4
