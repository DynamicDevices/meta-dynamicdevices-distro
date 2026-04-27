#!/bin/bash
# Auditd dispatcher plugin for CRA compliance
# This script is called by auditd when audit events occur
# It processes events and triggers the CRA audit handler

# Read audit event from stdin
while read -r line; do
    # Parse audit event type and key
    event_type=$(echo "$line" | grep -o 'type=[A-Z_]*' | cut -d'=' -f2)
    audit_key=$(echo "$line" | grep -o 'key="[^"]*"' | cut -d'"' -f2)
    
    # Only process CRA-relevant events (those with cra_ keys)
    if [[ "$audit_key" == cra_* ]]; then
        # Extract relevant information
        timestamp=$(echo "$line" | grep -o 'audit([0-9.]*' | cut -d'(' -f2)
        
        # Map audit keys to CRA event types
        case "$audit_key" in
            "cra_auth_events")
                cra_event_type="authentication_event"
                ;;
            "cra_user_changes")
                cra_event_type="user_management_change"
                ;;
            "cra_config_changes")
                cra_event_type="configuration_change"
                ;;
            "cra_privilege_escalation")
                cra_event_type="privilege_escalation"
                ;;
            "cra_network_changes")
                cra_event_type="network_configuration_change"
                ;;
            "cra_permission_changes")
                cra_event_type="file_permission_change"
                ;;
            "cra_security_changes")
                cra_event_type="security_module_change"
                ;;
            "cra_kernel_modules")
                cra_event_type="kernel_module_event"
                ;;
            "cra_failed_exec")
                cra_event_type="failed_execution"
                ;;
            *)
                cra_event_type="unknown_audit_event"
                ;;
        esac
        
        # Trigger CRA audit handler asynchronously
        /usr/sbin/cra-audit-handler.sh event "$cra_event_type" "$line" &
    fi
done
