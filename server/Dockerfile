# Use the official Ubuntu base image
FROM ubuntu:22.04 AS base

SHELL ["/bin/bash", "-c"]

# Set environment variables
ENV project=meeting-sdk-linux-sample
ENV cwd=/tmp/$project

# Set the working directory in the container
WORKDIR $cwd

ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    gdb \
    git \
    gfortran \
    libopencv-dev \
    libdbus-1-3 \
    libgbm1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libglib2.0-dev \
    libssl-dev \
    libx11-dev \
    libx11-xcb1 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-xfixes0 \
    libxcb-xtest0 \
    libgl1-mesa-dri \
    libxfixes3 \
    linux-libc-dev \
    pkgconf \
    tar \
    unzip \
    zip \
    ninja-build \
    wget \
    gnupg \
    pulseaudio \
    pulseaudio-utils \
    python3-pip \
    npm \
    xvfb && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install ALSA
RUN apt-get update && \
    apt-get install -y libasound2 libasound2-plugins alsa-utils alsa-oss pulseaudio pulseaudio-utils && \
    echo -e "pcm.!default {\n  type plug\n  slave.pcm \"hw:0,0\"\n}\nctl.!default {\n  type hw\n  card 0\n}" > /etc/asound.conf

# Copy the library files from zoom-sdk
COPY zoom-sdk/lib /lib

# Extract the Zoom SDK
COPY zoom-sdk/lib/zoom-meeting-sdk-linux_x86_64-6.3.0.6019.tar.xz /tmp/
RUN mkdir -p /lib/zoomsdk/ && \
    tar -xvf /tmp/zoom-meeting-sdk-linux_x86_64-6.3.0.6019.tar.xz -C /lib/zoomsdk || true

# Symlink libmeetingsdk.so.1 to libmeetingsdk.so
RUN ln -sf /lib/zoomsdk/libmeetingsdk.so /lib/zoomsdk/libmeetingsdk.so.1

# Add /lib/zoomsdk to ld.so.conf and refresh the linker cache
RUN echo "/lib/zoomsdk" >> /etc/ld.so.conf.d/zoomsdk.conf && ldconfig

# Create a user named zoomuser
RUN id -u zoomuser &>/dev/null || useradd -m zoomuser

# Change ownership of the /lib/zoomsdk directory to zoomuser and root
RUN chown -R zoomuser:zoomuser /lib/zoomsdk && \
    chown -R root:root /lib/zoomsdk && \
    find /lib/zoomsdk -type f -exec chmod +x {} \; || true

# Ensure the out directory exists and has the correct permissions
RUN mkdir -p /app/out && chown -R zoomuser:zoomuser /app/out

FROM base AS deps

ENV VCPKG_FORCE_SYSTEM_BINARIES=1

ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

WORKDIR /opt
RUN git clone --depth 1 https://github.com/Microsoft/vcpkg.git && \
    ./vcpkg/bootstrap-vcpkg.sh -disableMetrics && \
    ln -s /opt/vcpkg/vcpkg /usr/local/bin/vcpkg && \
    vcpkg install vcpkg-cmake ada-url cli11 jwt-cpp

# Give zoomuser and root access to /opt/vcpkg
RUN chown -R zoomuser:zoomuser /opt/vcpkg && \
    chown -R root:root /opt/vcpkg

FROM deps AS build

ENV VCPKG_FORCE_SYSTEM_BINARIES=1

WORKDIR /app

# Copy the entire project directory into the Docker image
COPY . /app

# Ensure start.sh is executable
RUN chmod +x /app/start.sh

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

RUN playwright install

# Compile the API server as root to avoid permission issues
USER root
RUN cmake -B build -S /app/zoom-sdk -DCMAKE_TOOLCHAIN_FILE=/opt/vcpkg/scripts/buildsystems/vcpkg.cmake && cmake --build build

# Ensure the build directory is copied to the final image
RUN mkdir -p /app/build && find build -mindepth 1 -maxdepth 1 -not -name 'CMakeCache.txt' -not -name 'CMakeFiles' -not -name 'Makefile' -not -name 'cmake_install.cmake' -not -name 'vcpkg-manifest-install.log' -not -name 'vcpkg_installed' -exec cp -r {} /app/build/ \;

# Expose the port that the app runs on
EXPOSE 7099

# Start pulseaudio as root to ensure necessary permissions
USER root

CMD ["bash", "-c", "cd /app && ./start.sh"]