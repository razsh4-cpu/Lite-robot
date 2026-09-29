import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "lite3_nav_test_override.py"
SPEC = importlib.util.spec_from_file_location("nav_test_override", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def state(tmp_path, score="0.75"):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE\n")
    (tmp_path / "LOCALIZATION_SCORE").write_text(score + "\n")


def test_default_is_normal_and_missing_token_is_inactive(tmp_path):
    assert MODULE.read(tmp_path) is None
    assert MODULE.NORMAL_THRESHOLD == 0.80
    assert MODULE.TEST_THRESHOLD == 0.70


def test_enable_requires_three_fresh_samples_and_none_source(tmp_path, monkeypatch):
    state(tmp_path)
    monkeypatch.setattr(MODULE.time, "sleep", lambda _seconds: None)
    value = MODULE.enable(tmp_path, "fixture", 120.0,)
    assert value["localization_samples"] == [0.75, 0.75, 0.75]
    assert MODULE.read(tmp_path) is not None
    (tmp_path / "COMMAND_SOURCE").write_text("LAPTOP_XBOX\n")
    try:
        MODULE.enable(tmp_path, "denied", 120.0)
    except RuntimeError as exc:
        assert "COMMAND_SOURCE" in str(exc)
    else:
        raise AssertionError("ownership conflict accepted")


def test_below_70_never_creates_override(tmp_path, monkeypatch):
    state(tmp_path, "0.699")
    monkeypatch.setattr(MODULE.time, "sleep", lambda _seconds: None)
    try:
        MODULE.enable(tmp_path, "denied", 120.0)
    except RuntimeError as exc:
        assert "BELOW TEST THRESHOLD" in str(exc)
    else:
        raise AssertionError("low localization accepted")
    assert MODULE.read(tmp_path) is None


def test_expiry_tamper_and_clear_restore_normal(tmp_path, monkeypatch):
    state(tmp_path)
    monkeypatch.setattr(MODULE.time, "sleep", lambda _seconds: None)
    value = MODULE.enable(tmp_path, "fixture", 30.0)
    assert MODULE.read(tmp_path, now=value["expires_unix"] + 0.1) is None
    payload = json.loads((tmp_path / MODULE.FILE_NAME).read_text())
    payload["threshold"] = 0.60
    (tmp_path / MODULE.FILE_NAME).write_text(json.dumps(payload))
    assert MODULE.read(tmp_path) is None
    MODULE.clear(tmp_path)
    MODULE.clear(tmp_path)
    assert not (tmp_path / MODULE.FILE_NAME).exists()


def test_override_ttl_is_bounded(tmp_path, monkeypatch):
    state(tmp_path)
    monkeypatch.setattr(MODULE.time, "sleep", lambda _seconds: None)
    value = MODULE.enable(tmp_path, "fixture", 9999.0)
    assert value["expires_unix"] - value["created_unix"] == MODULE.MAX_TTL_S
    assert MODULE.MAX_TTL_S == 180.0
