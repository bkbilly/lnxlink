# ---- Stage 1: The Builder ----
# Use the same base image to ensure compatibility of compiled libraries.
# We'll install build tools and our Python dependencies here.
FROM docker.io/python:3.12-slim-bookworm AS builder

# 1. Install build-time system dependencies
# - Use --no-install-recommends to avoid pulling in unnecessary packages.
# - libsystemd-dev is needed to compile against systemd, but we don't need the full systemd daemon.
# - Clean up apt cache in the same RUN layer to keep this stage smaller.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cmake \
        gcc \
        python3-dev \
        libsystemd-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. Consolidate all pip installs into a single layer for better caching and smaller size.
#    Using a virtual environment makes it trivial to copy the installed packages later.
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip --no-cache-dir install \
    docker \
    vdf \
    flask \
    waitress \
    jeepney \
    dbus-mediaplayer \
    dbus-notification \
    dbus-idle \
    ewmh \
    python-xlib \
    xlib-hotkeys \
    nvsmi \
    nvitop


# ---- Stage 2: The Final Image ----
# Start from a clean base image. It contains Python but none of the build tools.
FROM docker.io/python:3.12-slim-bookworm

WORKDIR /opt/lnxlink

# 1. Install only the essential RUNTIME system dependencies.
# - We don't need cmake, gcc, or python3-dev here.
# - dbus, xdg-utils, etc., are needed for the application to function.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        dbus \
        xdg-utils \
        xdotool \
        x11-xserver-utils && \
    rm -rf /var/lib/apt/lists/*

# 2. Copy the installed Python packages from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# 3. Copy your application code.
COPY . /opt/lnxlink

# 4. Activate the virtual environment and install your application.
#    This will be very fast as all dependencies are already in the venv.
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip --no-cache-dir install -e /opt/lnxlink

# 5. Define the container's runtime behavior.
ENTRYPOINT ["lnxlink", "-ie", "audio_select,bluetooth,boot_select,keep_alive,power_profile,screen_onoff,screenshot,speech_recognition,webcam,wifi"]
CMD ["-c", "/opt/lnxlink/config/config.yaml"]
