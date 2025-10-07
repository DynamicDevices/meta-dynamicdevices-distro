#
# LMP Feature: audit
# Comprehensive logging and audit framework for production security monitoring
#

CORE_IMAGE_BASE_INSTALL += " \
    audit \
    logrotate \
    rsyslog \
    systemd-analyze \
"

# Auto-enable critical audit and logging services
SYSTEMD_AUTO_ENABLE:pn-audit = "enable"
SYSTEMD_AUTO_ENABLE:pn-rsyslog = "enable"
