#
# DISTRO Feature: audit
# Comprehensive logging and audit framework for production security monitoring
#
# This feature provides:
# - System call auditing (audit package)
# - Advanced system logging (rsyslog)
# - Automated log rotation (logrotate)
# - System performance analysis (systemd-analyze)
#
# Usage: Add "audit" to DISTRO_FEATURES for boards requiring comprehensive logging
#

# Add audit and logging packages when audit feature is enabled
CORE_IMAGE_BASE_INSTALL:append = "${@bb.utils.contains('DISTRO_FEATURES', 'audit', ' audit logrotate rsyslog systemd-analyze', '', d)}"

# Auto-enable critical audit and logging services
SYSTEMD_AUTO_ENABLE:pn-audit = "${@bb.utils.contains('DISTRO_FEATURES', 'audit', 'enable', 'disable', d)}"
SYSTEMD_AUTO_ENABLE:pn-rsyslog = "${@bb.utils.contains('DISTRO_FEATURES', 'audit', 'enable', 'disable', d)}"

# Audit feature dependencies - ensure kernel audit support is enabled
DISTRO_FEATURES_BACKFILL_CONSIDERED:append = "${@bb.utils.contains('DISTRO_FEATURES', 'audit', ' audit-kernel', '', d)}"
