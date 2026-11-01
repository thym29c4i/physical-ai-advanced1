#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
if [ "$#" -ne 1 ]; then echo 'Usage: bash scripts/command.sh "受付まで荷物を届けて"'; exit 1; fi
payload=$(python3 -c 'import json,sys; print(json.dumps({"data": sys.argv[1]},ensure_ascii=False))' "$1")
ros2 topic pub --once /instruction std_msgs/msg/String "$payload"
