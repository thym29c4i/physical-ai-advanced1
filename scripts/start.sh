#!/usr/bin/env bash
set -eo pipefail
cd /project
source /opt/ros/humble/setup.bash
mkdir -p results
pids=()
cleanup() { kill "${pids[@]}" 2>/dev/null || true; wait || true; }
trap cleanup EXIT
trap 'exit 0' TERM INT
python3 app/train.py
Xvfb :1 -screen 0 1280x800x24 -ac & pids+=($!)
for n in {1..50}; do xdpyinfo -display :1 >/dev/null 2>&1 && break; sleep 0.2; done
xdpyinfo -display :1 >/dev/null
openbox --config-file worlds/openbox.xml >results/openbox.log 2>&1 & pids+=($!)
x11vnc -display :1 -nopw -forever -shared -rfbport 5900 -localhost >results/vnc.log 2>&1 & pids+=($!)
websockify --web=/usr/share/novnc/ 6080 localhost:5900 >results/web.log 2>&1 & pids+=($!)
ros2 run ros_gz_bridge parameter_bridge \
  '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist' \
  '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry' \
  >results/bridge.log 2>&1 & pids+=($!)
python3 -u app/controller.py >results/controller.log 2>&1 & pids+=($!)
ign gazebo -s -r -v 3 worlds/delivery.sdf >results/gazebo.log 2>&1 & pids+=($!)
# Start rendering after the server has created its scene.
for n in {1..30}; do
  if ign service -s /world/delivery/scene/info --reqtype ignition.msgs.Empty \
      --reptype ignition.msgs.Scene --timeout 1000 --req '' 2>/dev/null | grep -q 'model {'; then break; fi
  sleep 0.2
done
ign gazebo -g -v 3 --gui-config worlds/gui.config >results/gui.log 2>&1 & pids+=($!)
python3 -u app/panel.py >results/panel.log 2>&1 & pids+=($!)
echo 'Browser: http://localhost:6080/vnc.html?autoconnect=true&resize=scale'
wait -n "${pids[@]}"
