#!/usr/bin/env python3
"""Plot a one-leg-lift CSV. Reads files only; it has no robot transport."""

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def column(rows, name):
    return [float(row[name]) for row in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.trace.open(newline="") as stream:
        rows = list(csv.DictReader(stream))

    time = column(rows, "time_s")
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(time, [value * 57.2957795 for value in column(rows, "roll_rad")], label="roll")
    axes[0].plot(time, [value * 57.2957795 for value in column(rows, "pitch_rad")], label="pitch")
    axes[0].set_ylabel("body angle (deg)")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(time, [value * 1000.0 for value in column(rows, "fr_lift_m")], color="tab:purple")
    axes[1].axhline(5.0, color="black", linestyle="--", linewidth=0.8)
    axes[1].set_ylabel("FR lift (mm)")
    axes[1].grid(alpha=0.3)

    for key, label in (("fl_force_n", "FL"), ("fr_force_n", "FR"),
                       ("hl_force_n", "HL"), ("hr_force_n", "HR")):
        axes[2].plot(time, column(rows, key), label=label)
    axes[2].set_ylabel("normal force (N)")
    axes[2].set_xlabel("simulation time (s)")
    axes[2].legend(ncol=4)
    axes[2].grid(alpha=0.3)

    previous = None
    for row in rows:
        if row["state"] != previous:
            for axis in axes:
                axis.axvline(float(row["time_s"]), color="gray", alpha=0.18, linewidth=0.7)
            previous = row["state"]
    fig.suptitle("Lite3 simulated front-right leg lift")
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)


if __name__ == "__main__":
    main()
