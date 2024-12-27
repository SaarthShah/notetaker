# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN apt-get update && \
    apt-get install -y pulseaudio pulseaudio-utils dbus dbus-x11 wget gnupg xvfb && \
    apt-get install -y libnss3 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 libxrandr2 libasound2 libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    pip install --no-cache-dir -r requirements.txt && \
    useradd -m pulseaudio_user && \
    mkdir -p /var/run/pulse /var/lib/pulse /root/.config/pulse && \
    chown -R pulseaudio_user:pulseaudio_user /var/run/pulse /var/lib/pulse /root/.config/pulse

# Expose the port that the app runs on
EXPOSE 7099

RUN apt-get update && \
    apt-get install -y dbus-x11 pulseaudio upower && \
    rm -rf /var/lib/apt/lists/*

# Set environment variable for XDG_RUNTIME_DIR
ENV XDG_RUNTIME_DIR=/tmp/runtime-pulseaudio_user

# Start dbus and pulseaudio in the background
CMD ["bash", "-c", "service dbus start && su - pulseaudio_user -c 'pulseaudio --start' && export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket && xvfb-run -a google-chrome --no-sandbox --remote-debugging-port=9222 & uvicorn notetakers.app:app --host 0.0.0.0 --port 7099"]