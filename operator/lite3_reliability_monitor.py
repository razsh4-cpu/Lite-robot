#!/usr/bin/env python3
"""Tiny persistent Mini-PC health sampler, independent of ROS and networking."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import time

LOG_DIR = Path(os.environ.get(
    "LITE3_RELIABILITY_LOG_DIR", "/var/log/lite3-reliability"))
LOG_PATH = LOG_DIR / "health.jsonl"
MAX_BYTES = 20 * 1024 * 1024
INTERVAL_S = 15.0


def text(path, default=""):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return default


def integer(path):
    try:
        return int(text(path))
    except ValueError:
        return None


def memory():
    wanted = {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}
    result = {}
    for line in text("/proc/meminfo").splitlines():
        key, _, value = line.partition(":")
        if key in wanted:
            result[key] = int(value.strip().split()[0])
    return result


def temperatures():
    result = {}
    for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        value = integer(path)
        if value is not None:
            result[path.parent.name] = round(value / 1000.0, 1)
    return result


def interfaces():
    result = {}
    for path in Path("/sys/class/net").iterdir():
        if path.name == "lo":
            continue
        result[path.name] = {
            "operstate": text(path / "operstate", "unknown"),
            "carrier": integer(path / "carrier"),
            "rx_bytes": integer(path / "statistics/rx_bytes"),
            "tx_bytes": integer(path / "statistics/tx_bytes"),
            "rx_errors": integer(path / "statistics/rx_errors"),
            "tx_errors": integer(path / "statistics/tx_errors"),
            "rx_dropped": integer(path / "statistics/rx_dropped"),
            "tx_dropped": integer(path / "statistics/tx_dropped"),
        }
    return result


def top_processes():
    result = subprocess.run(
        ["ps", "-eo", "pid,comm,%cpu,%mem,rss", "--sort=-%cpu"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=3, check=False)
    return result.stdout.splitlines()[:9]


def sample():
    disk = shutil.disk_usage("/")
    return {
        "timestamp": time.time(),
        "boot_id": text("/proc/sys/kernel/random/boot_id", "unknown"),
        "uptime_s": float(text("/proc/uptime", "0").split()[0]),
        "loadavg": text("/proc/loadavg"),
        "memory_kib": memory(),
        "pressure_cpu": text("/proc/pressure/cpu"),
        "pressure_memory": text("/proc/pressure/memory"),
        "pressure_io": text("/proc/pressure/io"),
        "root_free_bytes": disk.free,
        "temperatures_c": temperatures(),
        "interfaces": interfaces(),
        "top_processes": top_processes(),
    }


def append(entry):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if LOG_PATH.exists() and LOG_PATH.stat().st_size >= MAX_BYTES:
        rotated = LOG_PATH.with_suffix(".jsonl.1")
        rotated.unlink(missing_ok=True)
        LOG_PATH.replace(rotated)
    with LOG_PATH.open("a", encoding="utf-8") as output:
        output.write(json.dumps(entry, sort_keys=True) + "\n")
        output.flush()
        os.fsync(output.fileno())


def main():
    while True:
        started = time.monotonic()
        try:
            append(sample())
        except Exception as error:  # diagnostics must not destabilize the host
            append({"timestamp": time.time(), "sampler_error": repr(error)})
        time.sleep(max(1.0, INTERVAL_S - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
