FROM ros:humble-ros-base-jammy
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-ros-gz ros-humble-nav-msgs ros-humble-geometry-msgs \
    ros-humble-std-msgs xvfb x11vnc novnc websockify openbox xterm \
    x11-utils ffmpeg fonts-noto-cjk libgl1-mesa-dri mesa-utils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /project
ENV DISPLAY=:1 LIBGL_ALWAYS_SOFTWARE=1 QT_X11_NO_MITSHM=1
ENTRYPOINT ["bash", "/project/scripts/start.sh"]
