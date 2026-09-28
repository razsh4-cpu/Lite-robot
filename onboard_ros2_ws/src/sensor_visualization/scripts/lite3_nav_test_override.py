#!/usr/bin/env python3
"""Manage one short-lived, operator-approved obstacle-test localization gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

NORMAL_THRESHOLD = 0.80
TEST_THRESHOLD = 0.70
MAX_TTL_S = 600.0
FILE_NAME = "NAV_TEST_OVERRIDE.json"


def path(state_dir: Path) -> Path:
    return state_dir / FILE_NAME


def read(state_dir: Path, now: float | None = None) -> dict | None:
    now = time.time() if now is None else float(now)
    try:
        value = json.loads(path(state_dir).read_text(encoding="utf-8"))
        samples = [float(item) for item in value["localization_samples"]]
        created = float(value["created_unix"])
        expires = float(value["expires_unix"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    valid = (
        value.get("purpose") == "obstacle_test"
        and value.get("operator_approved") is True
        and bool(value.get("session_id"))
        and float(value.get("threshold", -1.0)) == TEST_THRESHOLD
        and float(value.get("normal_threshold", -1.0)) == NORMAL_THRESHOLD
        and len(samples) >= 3
        and all(TEST_THRESHOLD <= item <= 1.0 for item in samples[-3:])
        and created <= now < expires
        and 0.0 < expires - created <= MAX_TTL_S
    )
    return value if valid else None


def score(state_dir: Path) -> float:
    score_path = state_dir / "LOCALIZATION_SCORE"
    value = float(score_path.read_text(encoding="utf-8").strip())
    if time.time() - score_path.stat().st_mtime > 2.5:
        raise RuntimeError("localization score is stale")
    return value


def enable(state_dir: Path, session_id: str, ttl_s: float) -> dict:
    source = (state_dir / "COMMAND_SOURCE").read_text(encoding="utf-8").strip()
    if source != "NONE":
        raise RuntimeError(f"COMMAND_SOURCE={source}")
    samples = []
    for index in range(3):
        samples.append(score(state_dir))
        if index != 2:
            time.sleep(1.05)
    if any(item < TEST_THRESHOLD for item in samples):
        raise RuntimeError(
            "TEST BLOCKED — LOCALIZATION BELOW TEST THRESHOLD: "
            + ", ".join(f"{100*item:.1f}%" for item in samples))
    now = time.time()
    ttl_s = min(MAX_TTL_S, max(30.0, float(ttl_s)))
    value = {
        "purpose": "obstacle_test",
        "session_id": session_id,
        "threshold": TEST_THRESHOLD,
        "normal_threshold": NORMAL_THRESHOLD,
        "operator_approved": True,
        "localization_samples": samples,
        "created_unix": now,
        "expires_unix": now + ttl_s,
    }
    target = path(state_dir)
    temporary = target.with_name("." + target.name + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)
    return value


def clear(state_dir: Path) -> None:
    try:
        path(state_dir).unlink()
    except FileNotFoundError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("enable", "status", "clear"))
    parser.add_argument("--state-dir", default="/run/lite3-control")
    parser.add_argument("--session")
    parser.add_argument("--ttl", type=float, default=600.0)
    args = parser.parse_args()
    state_dir = Path(args.state_dir)
    try:
        if args.command == "enable":
            if not args.session:
                raise RuntimeError("--session is required")
            value = enable(state_dir, args.session, args.ttl)
        elif args.command == "clear":
            clear(state_dir)
            value = None
        else:
            value = read(state_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"active": False, "error": str(exc)}))
        return 2
    print(json.dumps({"active": value is not None, "override": value}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
