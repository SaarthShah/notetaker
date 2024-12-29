# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install necessary packages, Chrome, and pulseaudio
RUN apt-get update && \
    apt-get install -y wget gnupg pulseaudio pulseaudio-utils && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Expose the port that the app runs on
EXPOSE 7099

# Start pulseaudio and the application
CMD ["bash", "-c", "pulseaudio --start && uvicorn notetakers.app:app --host 0.0.0.0 --port 7099 --reload"]