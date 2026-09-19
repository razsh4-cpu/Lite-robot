#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL="$ROOT/third_party/deep_robotics_model/Lite3/Lite3_mjcf/mjcf/Lite3.xml"
MUJOCO="$ROOT/third_party/mujoco/x86"

SRC="$ROOT/tools/one_leg_lift_sim_v2.cpp"
BIN="$ROOT/artifacts/fr_robustness/bin/one_leg_lift_sim_v2"
OUT="$ROOT/artifacts/fr_robustness"

mkdir -p "$OUT/bin" "$OUT/smoke" "$OUT/delay" "$OUT/noise" "$OUT/delay_noise"

export MUJOCO_COMPAT_ROOT="$MUJOCO"
export LD_LIBRARY_PATH="$MUJOCO/lib:${LD_LIBRARY_PATH:-}"

echo "=================================================="
echo " FR LEG ROBUSTNESS PIPELINE — SIMULATION ONLY"
echo "=================================================="
echo

if [[ ! -f "$SRC" ]]; then
    echo "ERROR: $SRC not found"
    exit 1
fi

if [[ ! -f "$MODEL" ]]; then
    echo "ERROR: model not found:"
    echo "$MODEL"
    exit 1
fi

echo "[1/5] Building V2..."

g++ -std=c++17 -O2 \
    "$SRC" \
    -I"$MUJOCO/include" \
    -I/usr/include/eigen3 \
    -I"$ROOT/tools" \
    -L"$MUJOCO/lib" \
    -Wl,-rpath,"$MUJOCO/lib" \
    -lmujoco \
    -o "$BIN"

echo "BUILD PASS"
echo

run_case() {
    local name="$1"
    local dir="$2"
    shift 2

    local case_dir="$dir/$name"
    mkdir -p "$case_dir"

    echo "--------------------------------------------------"
    echo "RUN: $name"
    echo "--------------------------------------------------"

    set +e
    "$BIN" \
        --model "$MODEL" \
        --output-dir "$case_dir" \
        --shift-x-mm 65 \
        --shift-y-mm 65 \
        --shift-s 2.0 \
        --hold-s 1.0 \
        --lift-mm 15 \
        --lift-s 1.5 \
        --lower-s 1.5 \
        --kp 180 \
        --kd 3.5 \
        "$@" \
        >"$case_dir/run.log" 2>&1

    local rc=$?
    set -e

    cat "$case_dir/run.log"

    if [[ $rc -eq 0 ]]; then
        echo "RESULT: PROCESS PASS"
    else
        echo "RESULT: PROCESS FAIL rc=$rc"
    fi

    echo
    return 0
}

echo "[2/5] Deterministic smoke tests..."

for seed in 1 2 3; do
    run_case \
        "baseline_seed_${seed}" \
        "$OUT/smoke" \
        --seed "$seed"
done

echo "[3/5] Delay sweep..."

for delay in 0 1 2 3 4 5; do
    run_case \
        "delay_${delay}ms" \
        "$OUT/delay" \
        --delay-ms "$delay" \
        --seed 1
done

echo "[4/5] Noise sweep..."

for noise in 0 0.001 0.002 0.003 0.004; do
    safe_noise="${noise//./p}"

    for seed in 1 2 3; do
        run_case \
            "noise_${safe_noise}_seed_${seed}" \
            "$OUT/noise" \
            --sensor-noise-rad "$noise" \
            --seed "$seed"
    done
done

echo "[5/5] Combined delay + noise map..."

for delay in 0 1 2 3 4 5; do
    for noise in 0 0.001 0.002 0.003 0.004; do
        safe_noise="${noise//./p}"

        for seed in 1 2 3; do
            run_case \
                "delay_${delay}ms_noise_${safe_noise}_seed_${seed}" \
                "$OUT/delay_noise" \
                --delay-ms "$delay" \
                --sensor-noise-rad "$noise" \
                --seed "$seed"
        done
    done
done

echo
echo "=================================================="
echo " PIPELINE FINISHED"
echo "=================================================="
echo
echo "Results:"
echo "$OUT"
echo
echo "SIMULATION ONLY."
echo "NO HARDWARE COMMANDS WERE EXECUTED."
