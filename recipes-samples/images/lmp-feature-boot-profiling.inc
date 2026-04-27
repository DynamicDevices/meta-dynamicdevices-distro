# Boot profiling feature for Dynamic Devices boards
# Enables comprehensive boot time analysis tools and configuration
# Target: 1-2 second boot time optimization

SUMMARY = "Boot profiling feature for Dynamic Devices boards"

# Core boot profiling tools
CORE_IMAGE_BASE_INSTALL += " \
    boot-profiling \
    systemd-analyze \
    bc \
    procps \
"

# Additional debugging tools when boot profiling is enabled
CORE_IMAGE_BASE_INSTALL += " \
    strace \
    perf \
    iotop \
    htop \
"

# Kernel modules for detailed profiling
CORE_IMAGE_BASE_INSTALL += " \
    kernel-module-configs \
"
