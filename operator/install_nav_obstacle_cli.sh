#!/usr/bin/env bash
# Install laptop-only operator wrappers. Starts no service and sends no command.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.local/bin"
ln -sfn "$script_dir/lite3_nav_cli.py" "$HOME/.local/bin/nav"
ln -sfn "$script_dir/lite3_command_registry.py" "$HOME/.local/bin/commands"
chmod +x "$script_dir/lite3_nav_cli.py" \
  "$script_dir/lite3_nav_obstacle_execute.py" \
  "$script_dir/lite3_nav_obstacle_cancel.py" \
  "$script_dir/lite3_publish_obstacle_plan.py" \
  "$script_dir/lite3_chair_dryrun_snapshot.py" \
  "$script_dir/lite3_chair_snapshot_analyze.py" \
  "$script_dir/lite3_command_registry.py"
echo "LITE3 OBSTACLE TEST CLI INSTALLED — NO ROBOT COMMAND SENT"
