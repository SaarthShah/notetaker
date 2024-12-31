#!/usr/bin/env bash

# Check if meeting number and password are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <meeting_number> <password>"
  exit 1
fi

MEETING_NUMBER=$1
PASSWORD=$2

# directory for CMake output
BUILD=build

# directory for application output
mkdir -p out

setup-pulseaudio() {
  # Enable dbus
  if [[  ! -d /var/run/dbus ]]; then
    mkdir -p /var/run/dbus
    dbus-uuidgen > /var/lib/dbus/machine-id
    dbus-daemon --config-file=/usr/share/dbus-1/system.conf --print-address
  fi

  usermod -G pulse-access,audio root

  # Cleanup to be "stateless" on startup, otherwise pulseaudio daemon can't start
  rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse/
  mkdir -p ~/.config/pulse/ && cp -r /etc/pulse/* "$_"

  pulseaudio -D --exit-idle-time=-1 --system --disallow-exit

  # Create a virtual speaker output

  pactl load-module module-null-sink sink_name=SpeakerOutput
  pactl set-default-sink SpeakerOutput
  pactl set-default-source SpeakerOutput.monitor

  # Make config file
  echo -e "[General]\nsystem.audio.type=default" > ~/.config/zoomus.conf
}

build() {
  # Only configure CMake if this is the first run
  if [[ ! -d "$BUILD" ]]; then
    echo "Building the project..."
    cmake -B "$BUILD" -S . --preset debug || exit
    npm --prefix=client install
  else
    echo "Build directory already exists. Skipping build."
  fi

  # Correct the path for the shared library
  LIB="/lib/zoomsdk/libmeetingsdk.so"
  [[ ! -f "${LIB}.1" ]] && cp "$LIB"{,.1}

  # Set up and start pulseaudio
  setup-pulseaudio &> /dev/null || exit
}

run() {
    # Use the meeting number and password to start/join the meeting
    echo "Starting meeting with number: $MEETING_NUMBER and password: $PASSWORD"
    exec ./"$BUILD"/zoomsdk --meeting-number "$MEETING_NUMBER" --password "$PASSWORD"
}

build && run

exit $?
