#!/bin/bash
# CRA Audit Event Handler - Real-time audit event detection and upload
# EU Cyber Resilience Act compliance for Foundries.io devices
# Usage: cra-audit-handler.sh <command> [arguments]

set -e

# Configuration (can be overridden by /etc/default/cra-audit)
FACTORY="${FACTORY:-dynamic-devices}"
DEVICE_NAME="${DEVICE_NAME:-$(hostname)}"
AUDIT_QUEUE_DIR="${AUDIT_QUEUE_DIR:-/var/sota/audit-queue}"
AUDIT_UPLOADED_DIR="${AUDIT_UPLOADED_DIR:-/var/sota/audit-uploaded}"
AUDIT_LOG_FILE="${AUDIT_LOG_FILE:-/var/log/cra-audit-events.log}"
CONNECTIVITY_CHECK_URL="${CONNECTIVITY_CHECK_URL:-https://ota-lite.foundries.io:8443}"

# Load configuration if available
[ -f /etc/default/cra-audit ] && source /etc/default/cra-audit

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_audit() {
    local level="$1"
    local message="$2"
    local timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "[$timestamp] [$level] $message" | tee -a "$AUDIT_LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log_audit "INFO" "$1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log_audit "SUCCESS" "$1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_audit "ERROR" "$1"
}

# Initialize audit system
init_audit_system() {
    mkdir -p "$AUDIT_QUEUE_DIR" "$AUDIT_UPLOADED_DIR"
    touch "$AUDIT_LOG_FILE"
    log_info "CRA audit system initialized"
}

# Check internet connectivity
check_internet_connectivity() {
    curl -s --connect-timeout 5 --max-time 10 \
        --cert /var/sota/client.pem \
        --key /var/sota/pkey.pem \
        --cacert /var/sota/root.crt \
        "$CONNECTIVITY_CHECK_URL" >/dev/null 2>&1
}

# Get current target name (like fiotest does)
get_current_target() {
    if [ -f "/var/sota/current-target" ]; then
        grep "TARGET_NAME" /var/sota/current-target | cut -d'=' -f2 | tr -d '"' | tr -d ' '
    else
        echo "unknown-target"
    fi
}

# Get test API URL (like fiotest does)
get_test_url() {
    if [ -f "/var/sota/sota.toml" ]; then
        grep "^server =" /var/sota/sota.toml | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d ' ' | sed 's|$|/tests|'
    else
        echo "https://ota-lite.foundries.io:8443/tests"
    fi
}

# Generate unique audit event ID
generate_audit_id() {
    echo "audit-$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)"
}

# Get event severity
get_event_severity() {
    local event_type="$1"
    case "$event_type" in
        "security_breach"|"unauthorized_access"|"system_compromise")
            echo "CRITICAL"
            ;;
        "authentication_failure"|"service_failure"|"configuration_change")
            echo "HIGH"
            ;;
        "suspicious_activity"|"performance_degradation")
            echo "MEDIUM"
            ;;
        *)
            echo "LOW"
            ;;
    esac
}

# Create audit report
create_audit_report() {
    local event_type="$1"
    local event_details="$2"
    local audit_id="$3"
    local timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    local audit_file="$AUDIT_QUEUE_DIR/$audit_id.json"
    
    cat > "$audit_file" <<EOF
{
    "audit_event": {
        "id": "$audit_id",
        "timestamp": "$timestamp",
        "device_id": "$DEVICE_NAME",
        "event_type": "$event_type",
        "compliance_framework": "EU_CRA",
        "severity": "$(get_event_severity "$event_type")",
        "details": "$event_details",
        "system_context": {
            "kernel_version": "$(uname -r)",
            "lmp_version": "$(cat /etc/os-release | grep VERSION_ID | cut -d'=' -f2 | tr -d '\"' 2>/dev/null || echo 'unknown')",
            "uptime": "$(uptime)",
            "memory_usage": "$(free -m | grep Mem | awk '{print $3"/"$2" MB"}' 2>/dev/null || echo 'unknown')"
        }
    }
}
EOF
    
    echo "$audit_file"
}

# Upload audit report using fiotest API
upload_audit_report() {
    local audit_file="$1"
    local audit_id="$(basename "$audit_file" .json)"
    
    if [ ! -f "$audit_file" ]; then
        log_error "Audit file not found: $audit_file"
        return 1
    fi
    
    log_info "Uploading CRA audit report: $audit_id"
    
    # Get target and URL info
    local current_target
    current_target=$(get_current_target)
    local test_url
    test_url=$(get_test_url)
    
    # Create CRA-specific test name
    local test_name="cra-audit-compliance-$audit_id"
    local start_payload="{\"name\": \"$test_name\"}"
    
    local test_id
    test_id=$(curl -s \
        --cert /var/sota/client.pem \
        --key /var/sota/pkey.pem \
        --cacert /var/sota/root.crt \
        -H "Content-Type: application/json" \
        -H "x-ats-target: $current_target" \
        -X POST \
        -d "$start_payload" \
        "$test_url" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$test_id" ]; then
        log_success "CRA audit uploaded successfully: $test_id"
        
        # Move to uploaded directory to prevent re-upload
        mv "$audit_file" "$AUDIT_UPLOADED_DIR/"
        return 0
    else
        log_error "Failed to upload CRA audit: $audit_id"
        return 1
    fi
}

# Process audit event
process_audit_event() {
    local event_type="$1"
    local event_details="$2"
    
    if [ -z "$event_type" ]; then
        log_error "Event type is required"
        return 1
    fi
    
    local audit_id
    audit_id=$(generate_audit_id)
    
    log_info "Processing CRA audit event: $event_type (ID: $audit_id)"
    
    # Create audit report
    local audit_file
    audit_file=$(create_audit_report "$event_type" "$event_details" "$audit_id")
    
    if [ ! -f "$audit_file" ]; then
        log_error "Failed to create audit report"
        return 1
    fi
    
    # Check internet connectivity and upload immediately if possible
    if check_internet_connectivity; then
        log_info "Internet connection available - uploading immediately"
        if upload_audit_report "$audit_file"; then
            log_success "Immediate CRA audit upload successful: $audit_id"
        else
            log_error "Immediate upload failed - audit queued for later"
        fi
    else
        log_info "No internet connection - CRA audit queued for later upload"
    fi
}

# Process queued audit reports
process_audit_queue() {
    if [ ! -d "$AUDIT_QUEUE_DIR" ]; then
        return 0
    fi
    
    local queued_reports
    queued_reports=$(find "$AUDIT_QUEUE_DIR" -name "*.json" -type f | wc -l)
    
    if [ "$queued_reports" -eq 0 ]; then
        log_info "No queued CRA audit reports to process"
        return 0
    fi
    
    log_info "Processing $queued_reports queued CRA audit reports"
    
    # Check internet connectivity
    if ! check_internet_connectivity; then
        log_info "No internet connection - keeping CRA audits in queue"
        return 0
    fi
    
    local uploaded=0
    local failed=0
    
    for audit_file in "$AUDIT_QUEUE_DIR"/*.json; do
        if [ -f "$audit_file" ]; then
            local audit_id
            audit_id=$(basename "$audit_file" .json)
            
            if upload_audit_report "$audit_file"; then
                ((uploaded++))
                log_success "Uploaded queued CRA audit: $audit_id"
            else
                ((failed++))
                log_error "Failed to upload queued CRA audit: $audit_id"
            fi
        fi
    done
    
    log_info "CRA audit queue processing complete: $uploaded uploaded, $failed failed"
}

# Monitor for audit events
monitor_audit_events() {
    log_info "Starting CRA audit event monitoring"
    
    # Monitor system logs for audit events
    journalctl -f -p err --since now | while read -r line; do
        if echo "$line" | grep -qE "(authentication failure|permission denied|unauthorized|breach|compromise)"; then
            process_audit_event "security_event" "$line" &
        elif echo "$line" | grep -qE "(service.*failed|daemon.*died|critical error)"; then
            process_audit_event "service_failure" "$line" &
        fi
    done
}

# Main function
main() {
    local command="$1"
    shift
    
    init_audit_system
    
    case "$command" in
        "event")
            process_audit_event "$@"
            ;;
        "queue")
            process_audit_queue
            ;;
        "monitor")
            monitor_audit_events
            ;;
        "test")
            process_audit_event "cra_compliance_test" "CRA audit system test - $(date)"
            ;;
        *)
            cat <<EOF
CRA Audit Event Handler for EU Cyber Resilience Act Compliance

Usage: $0 <command> [arguments]

Commands:
  event <type> <details>  - Process a CRA audit event
  queue                   - Process queued audit reports  
  monitor                 - Start real-time monitoring
  test                    - Test the CRA audit system

Examples:
  $0 event security_breach "Unauthorized access attempt"
  $0 event service_failure "SSH daemon crashed"
  $0 queue
  $0 monitor
  $0 test

EOF
            exit 1
            ;;
    esac
}

main "$@"
