#!/usr/bin/env bash

# directory for CMake output
BUILD=build

# directory for application output
mkdir -p out

setup-pulseaudio() {
  echo "Setting up PulseAudio..."
  
  # Enable dbus
  if [[ ! -d /var/run/dbus ]]; then
    echo "Creating /var/run/dbus directory..."
    mkdir -p /var/run/dbus
    echo "Generating dbus machine-id..."
    dbus-uuidgen > /var/lib/dbus/machine-id
    echo "Starting dbus-daemon..."
    dbus-daemon --config-file=/usr/share/dbus-1/system.conf --print-address
  fi

  echo "Adding root to pulse-access and audio groups..."
  usermod -G pulse-access,audio root

  # Cleanup to be "stateless" on startup, otherwise pulseaudio daemon can't start
  echo "Cleaning up PulseAudio state..."
  rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse/
  mkdir -p ~/.config/pulse/ && cp -r /etc/pulse/* "$_"

  echo "Starting PulseAudio daemon..."
  pulseaudio -D --exit-idle-time=-1 --system --disallow-exit

  # Create a virtual speaker output
  echo "Loading module-null-sink for virtual speaker output..."
  pactl load-module module-null-sink sink_name=SpeakerOutput
  echo "Setting default sink to SpeakerOutput..."
  pactl set-default-sink SpeakerOutput
  echo "Setting default source to SpeakerOutput.monitor..."
  pactl set-default-source SpeakerOutput.monitor

  # Make config file
  echo "Creating zoomus.conf configuration file..."
  echo -e "[General]\nsystem.audio.type=default" > ~/.config/zoomus.conf
}

build() {
  echo "Starting build process..."
  
  # Configure CMake if this is the first run
  if [[ ! -d "$BUILD" ]]; then
    echo "Configuring CMake..."
    cmake -B "$BUILD" -S . --preset debug || exit
    echo "Installing npm packages for client..."
    npm --prefix=client install
  fi

  # Rename the shared library
  LIB="lib/zoomsdk/libmeetingsdk.so"
  if [[ ! -f "${LIB}.1" ]]; then
    echo "Renaming shared library..."
    cp "$LIB"{,.1}
  fi

  # Set up and start pulseaudio
  echo "Setting up and starting PulseAudio..."
  setup-pulseaudio &> /dev/null || exit

  # Build the Source Code
  echo "Building the source code..."
  cmake --build "$BUILD"
}

run() {
  echo "Running the application..."
  exec ./"$BUILD"/zoomsdk
}

echo "Initiating build and run sequence..."
build && run

exit_code=$?
echo "Script exited with code $exit_code"
exit $exit_code
