#!/usr/bin/env python3
"""Fail closed unless the live map localization is fresh and validated."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lite3_nav_test_override import read as read_test_override


def localization_ready(state_dir: Path, minimum: float = 0.80,
                       max_age: float = 2.5, now: float | None = None):
    now = time.time() if now is None else float(now)
    state_path = state_dir / "LOCALIZATION_STATE"
    score_path = state_dir / "LOCALIZATION_SCORE"
    startup_path = state_dir / "LOCALIZATION_STARTUP_STATE"
    try:
        state = state_path.read_text(encoding="utf-8").strip()
        score = float(score_path.read_text(encoding="utf-8").strip())
        startup = startup_path.read_text(encoding="utf-8").strip()
        age = max(now - state_path.stat().st_mtime,
                  now - score_path.stat().st_mtime)
    except (OSError, ValueError) as exc:
        return False, 0.0, f"localization status unavailable: {exc}"
    if startup != "NAVIGATION_READY":
        return False, score, f"localization startup state: {startup}"
    if age < 0.0 or age > max_age:
        return False, score, f"localization status stale ({age:.1f}s)"
    if state != "LOCALIZED" or score < minimum:
        return False, score, f"UNLOCALIZED ({100.0 * score:.1f}% < {100.0 * minimum:.0f}%)"
    return True, score, f"LOCALIZED ({100.0 * score:.1f}%)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default="/run/lite3-control")
    parser.add_argument("--minimum", type=float, default=0.80)
    parser.add_argument("--max-age", type=float, default=2.5)
    args = parser.parse_args()
    state_dir = Path(args.state_dir)
    override = read_test_override(state_dir)
    minimum = float(override["threshold"]) if override else args.minimum
    ready, _score, reason = localization_ready(
        state_dir, minimum, args.max_age)
    if override:
        reason = "TEST OVERRIDE ACTIVE — " + reason
    print(reason)
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
