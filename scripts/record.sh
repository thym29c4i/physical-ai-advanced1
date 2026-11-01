#!/usr/bin/env bash
set -eo pipefail
cd /project
duration=${1:-120}
if ! [[ "$duration" =~ ^[0-9]+$ ]] || (( duration < 60 || duration > 180 )); then
  echo 'Duration must be 60–180 seconds.'; exit 1
fi
mkdir -p results
ffmpeg -n -video_size 1280x800 -framerate 20 -f x11grab -i :1.0 \
  -t "$duration" -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p \
  "results/demo-$(date +%Y%m%d-%H%M%S).mp4"
