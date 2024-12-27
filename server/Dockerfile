# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install necessary packages, Chrome, pulseaudio, and v4l2loopback
RUN apt-get update && \
    apt-get install -y wget gnupg pulseaudio pulseaudio-utils v4l2loopback-dkms ffmpeg dbus-x11 && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Expose the port that the app runs on
EXPOSE 7099

# Start pulseaudio, create virtual devices, and run the application
CMD ["bash", "-c", "pulseaudio --system --disallow-exit --exit-idle-time=-1 && modprobe v4l2loopback && ffmpeg -f lavfi -i color=c=black:s=640x480:r=30 -f v4l2 /dev/video0 & pactl load-module module-null-sink sink_name=VirtualMic && pactl load-module module-loopback source=VirtualMic.monitor && uvicorn notetakers.app:app --host 0.0.0.0 --port 7099"]