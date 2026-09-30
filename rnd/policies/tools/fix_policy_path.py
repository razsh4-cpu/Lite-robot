from pathlib import Path
import os
import sys

repo = Path.cwd()

real_model = repo / "policy" / "ppo" / "policy.onnx"
expected_model = repo.parent / "policy" / "ppo" / "policy.onnx"

print(f"Repository: {repo}")
print(f"Real model: {real_model}")
print(f"Expected by console: {expected_model}")

if not real_model.exists():
    print("ERROR: real policy.onnx was not found.")
    sys.exit(1)

expected_model.parent.mkdir(parents=True, exist_ok=True)

if expected_model.exists() or expected_model.is_symlink():
    if expected_model.is_symlink():
        target = expected_model.resolve()
        if target == real_model.resolve():
            print("Symlink already correct. Nothing to do.")
            sys.exit(0)

        print(f"Removing incorrect symlink: {expected_model}")
        expected_model.unlink()
    else:
        print(
            "ERROR: a real file already exists at the expected path.\n"
            "Not overwriting it automatically."
        )
        sys.exit(1)

os.symlink(real_model.resolve(), expected_model)

print("Created symlink:")
print(f"{expected_model} -> {real_model.resolve()}")

if expected_model.resolve() != real_model.resolve():
    print("ERROR: symlink verification failed.")
    sys.exit(1)

print("PASS: policy path fixed successfully.")
print("No robot command was executed.")
