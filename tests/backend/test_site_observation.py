import os
from types import SimpleNamespace
from backend.lite3.observation import ReadinessTracker, sample_guard_files
from backend.lite3.observation import RosObservation
from backend.lite3.site_map import map_grid_matches


def test_distinct_guard_file_updates_not_repeat_reads(tmp_path):
    tracker = ReadinessTracker("site")
    for name, value in (("LOCALIZATION_STATE", "LOCALIZED"),
                        ("LOCALIZATION_SCORE", "0.91"),
                        ("LOCALIZATION_STARTUP_STATE", "NAVIGATION_READY")):
        path = tmp_path / name
        path.write_text(value)
        os.utime(path, (100, 100))
    for _ in range(3):
        sample_guard_files(tracker, tmp_path, 10, 100)
    assert len(tracker.samples) == 1
    sample_guard_files(tracker, tmp_path, 10.10001, 100.1)
    assert len(tracker.samples) == 1
    for stamp in (100.5, 101):
        for path in tmp_path.iterdir(): os.utime(path, (stamp, stamp))
        sample_guard_files(tracker, tmp_path, stamp - 90, stamp)
    assert len(tracker.samples) == 3
    sample_guard_files(tracker, tmp_path, 15, 105)
    assert not tracker.samples


def test_map_grid_detects_disk_change_without_server_reload(tmp_path):
    image = tmp_path / "map.pgm"
    image.write_bytes(b"P5\n2 1\n255\n\xff\x00")
    metadata = tmp_path / "map.yaml"
    metadata.write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n")
    origin = SimpleNamespace(position=SimpleNamespace(x=0, y=0, z=0),
                             orientation=SimpleNamespace(x=0, y=0, z=0, w=1))
    grid = SimpleNamespace(header=SimpleNamespace(frame_id="map"), data=[0, 100],
                           info=SimpleNamespace(width=2, height=1, resolution=0.05, origin=origin))
    assert map_grid_matches(metadata, grid)
    image.write_bytes(b"P5\n2 1\n255\n\x00\x00")
    assert not map_grid_matches(metadata, grid)


def test_scan_freshness_uses_source_age_not_receipt_age(monkeypatch):
    observer = RosObservation.__new__(RosObservation)
    observer.tracker = ReadinessTracker("site")
    observer.node = SimpleNamespace(get_clock=lambda: SimpleNamespace(now=lambda:
                                    SimpleNamespace(nanoseconds=10_000_000_000)))
    msg = SimpleNamespace(header=SimpleNamespace(stamp=SimpleNamespace(sec=9, nanosec=10_000_000)))
    monkeypatch.setattr("backend.lite3.observation.time.monotonic", lambda: 10)
    observer.sensor("scan", msg)
    assert observer.tracker.observations["scan"][1] == 9.01


def test_map_grid_uses_vertical_image_flip(tmp_path):
    image = tmp_path / "map.pgm"
    image.write_bytes(b"P5\n1 2\n255\n\xff\x00")
    metadata = tmp_path / "map.yaml"
    metadata.write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n")
    origin = SimpleNamespace(position=SimpleNamespace(x=0, y=0, z=0),
                             orientation=SimpleNamespace(x=0, y=0, z=0, w=1))
    grid = SimpleNamespace(header=SimpleNamespace(frame_id="map"), data=[100, 0],
                           info=SimpleNamespace(width=1, height=2, resolution=0.05, origin=origin))
    assert map_grid_matches(metadata, grid)
    grid.data = [0, 100]
    assert not map_grid_matches(metadata, grid)
