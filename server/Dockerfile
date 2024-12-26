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

# Setup virtual audio drivers
RUN useradd -m pulseaudio_user && \
    mkdir -p /var/run/pulse /var/lib/pulse /root/.config/pulse && \
    chown -R pulseaudio_user:pulseaudio_user /var/run/pulse /var/lib/pulse /root/.config/pulse && \
    su pulseaudio_user -c "pulseaudio -D --verbose --exit-idle-time=-1 --system --disallow-exit" && \
    su pulseaudio_user -c "pactl load-module module-null-sink sink_name=DummyOutput sink_properties=device.description='Virtual_Dummy_Output'" && \
    su pulseaudio_user -c "pactl load-module module-null-sink sink_name=MicOutput sink_properties=device.description='Virtual_Microphone_Output'" && \
    su pulseaudio_user -c "pactl set-default-source MicOutput.monitor" && \
    su pulseaudio_user -c "pactl set-default-sink MicOutput" && \
    su pulseaudio_user -c "pactl load-module module-virtual-source source_name=VirtualMic"

# Expose the port that the app runs on
EXPOSE 7099

# Run the application
CMD ["uvicorn", "notetakers.app:app", "--host", "0.0.0.0", "--port", "7099"]