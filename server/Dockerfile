# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN apt-get update && \
    apt-get install -y pulseaudio && \
    pip install --no-cache-dir -r requirements.txt

# Setup virtual audio drivers and install Google Chrome
RUN apt-get update && \
    apt-get install -y pulseaudio pulseaudio-utils dbus dbus-x11 wget gnupg && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    useradd -m pulseaudio_user && \
    mkdir -p /var/run/pulse /var/lib/pulse /root/.config/pulse && \
    chown -R pulseaudio_user:pulseaudio_user /var/run/pulse /var/lib/pulse /root/.config/pulse

# Expose the port that the app runs on
EXPOSE 7099

# Run the application
CMD ["uvicorn", "notetakers.app:app", "--host", "0.0.0.0", "--port", "7099"]