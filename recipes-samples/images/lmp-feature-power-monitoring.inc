# Power Monitoring and Analysis Tools Feature - DEVELOPMENT ONLY
# Include this feature to add comprehensive power monitoring tools to development images
# This feature should only be enabled for development builds with debug-tweaks

SUMMARY = "Power monitoring and analysis tools for development and optimization"

# Core power monitoring tools
IMAGE_INSTALL:append = " \
    powertop \
    iotop \
    htop \
    sysstat \
    perf \
    power-analysis-suite \
"

# System analysis and profiling tools
IMAGE_INSTALL:append = " \
    strace \
    ltrace \
    lsof \
    procps \
    psmisc \
    util-linux \
"

# Hardware monitoring and control tools
IMAGE_INSTALL:append = " \
    i2c-tools \
    spitools \
    devmem2 \
    libgpiod-tools \
    gpio-utils \
"

# Network monitoring for WiFi power analysis
IMAGE_INSTALL:append = " \
    tcpdump \
    netstat \
    ss \
    ethtool \
    wireless-tools \
    iw \
"

# Kernel debugging and tracing tools
IMAGE_INSTALL:append = " \
    trace-cmd \
    kernelshark \
    ftrace \
"

# File system and I/O monitoring
IMAGE_INSTALL:append = " \
    iotop \
    iostat \
    vmstat \
    pv \
"

# Temperature and thermal monitoring
IMAGE_INSTALL:append = " \
    lm-sensors \
    sensors \
"

# Power management utilities
IMAGE_INSTALL:append = " \
    cpufrequtils \
    pm-utils \
    upower \
"

# Development and debugging essentials
IMAGE_INSTALL:append = " \
    gdb \
    gdbserver \
    valgrind \
    binutils \
"

# Scripting and automation tools
IMAGE_INSTALL:append = " \
    python3 \
    python3-modules \
    bash \
    bc \
    jq \
"

# Additional kernel modules for power monitoring
IMAGE_INSTALL:append = " \
    kernel-module-cpufreq-stats \
    kernel-module-cpufreq-userspace \
    kernel-module-thermal \
"

FEATURE_DESCRIPTION = "Comprehensive power monitoring and analysis tools for development and optimization"
