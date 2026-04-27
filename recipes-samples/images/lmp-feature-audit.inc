#
# LMP Feature: audit
# Comprehensive logging and audit framework for production security monitoring
# Includes CRA compliance audit system for EU Cyber Resilience Act
#

CORE_IMAGE_BASE_INSTALL += " \
    audit \
    logrotate \
    rsyslog \
    systemd-analyze \
"

# Add CRA audit system for EU Cyber Resilience Act compliance
CORE_IMAGE_BASE_INSTALL += "${@bb.utils.contains('DISTRO_FEATURES', 'cra-audit', 'cra-audit-system', '', d)}"

# Auto-enable critical audit and logging services
SYSTEMD_AUTO_ENABLE:pn-audit = "enable"
SYSTEMD_AUTO_ENABLE:pn-rsyslog = "enable"
SYSTEMD_AUTO_ENABLE:pn-cra-audit-system = "enable"
