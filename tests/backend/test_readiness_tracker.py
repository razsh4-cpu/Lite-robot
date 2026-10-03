import pytest
from backend.lite3.observation import ReadinessTracker


def populated(now=10):
    tracker = ReadinessTracker("sha256:site")
    for name in tracker.required:
        tracker.update(name, True, now)
    tracker.active_map_identity = "sha256:site"
    for stamp in (9.8, 9.9, 10):
        tracker.localization(0.9, "LOCALIZED", stamp)
    return tracker


def test_three_distinct_measurements_required():
    tracker = populated()
    assert tracker.ready("NONE", 10).localization_samples == (0.9, 0.9, 0.9)
    tracker.samples.clear()
    for _ in range(3):
        tracker.localization(0.9, "LOCALIZED", 10)
    with pytest.raises(ValueError):
        tracker.ready("NONE", 10)


@pytest.mark.parametrize("fault", ["stale", "wrong_map", "unlocalized", "low", "nan", "tf"])
def test_live_failures_block_readiness(fault):
    tracker = populated()
    if fault == "stale":
        now = 15
    else:
        now = 10
    if fault == "wrong_map": tracker.active_map_identity = "sha256:other"
    if fault == "unlocalized": tracker.localization(0.95, "UNLOCALIZED", 10.1)
    if fault == "low": tracker.localization(0.79, "LOCALIZED", 10.1)
    if fault == "nan": tracker.localization(float("nan"), "LOCALIZED", 10.1)
    if fault == "tf": tracker.update("tf", False, 10)
    with pytest.raises(ValueError):
        tracker.ready("NONE", now)


def test_stale_localization_never_becomes_current_by_polling():
    tracker = populated()
    for name in tracker.required:
        tracker.update(name, True, 15)
    with pytest.raises(ValueError):
        tracker.ready("NONE", 15)


def test_stale_mission_state_blocks_even_with_fresh_other_inputs():
    tracker = populated()
    for name in tracker.required:
        if name != "mission_clear": tracker.update(name, True, 14)
    for stamp in (13.8, 13.9, 14): tracker.localization(0.9, "LOCALIZED", stamp)
    with pytest.raises(ValueError, match="mission_clear"):
        tracker.ready("NONE", 14)
