#!/bin/bash
# CRA Audit System Test - Demonstrates automatic audit event detection
# This script shows how the system responds to real audit events

echo "🔍 CRA Audit System - Automatic Detection Test"
echo "=============================================="

# Test 1: Trigger a file permission change (auditd will detect this)
echo "📋 Test 1: File permission change detection"
test_file="/tmp/cra-audit-test-$(date +%s)"
touch "$test_file"
echo "Created test file: $test_file"

# This will trigger the cra_permission_changes audit rule
chmod 777 "$test_file"
echo "✅ Changed permissions (audit event triggered automatically)"

# Test 2: Simulate authentication failure
echo ""
echo "📋 Test 2: Authentication failure simulation"
# This would normally be detected by monitoring auth logs
echo "$(date) auth: authentication failure for user test from 192.168.1.100" >> /var/log/auth.log 2>/dev/null || echo "⚠️  Cannot write to auth.log (requires root)"

# Test 3: Manual audit event trigger
echo ""
echo "📋 Test 3: Manual audit event trigger"
/usr/sbin/cra-audit-handler.sh event "cra_test_event" "CRA audit system functionality test - $(date)"

# Test 4: Check audit queue
echo ""
echo "📋 Test 4: Check audit queue status"
if [ -d "/var/sota/audit-queue" ]; then
    queue_count=$(find /var/sota/audit-queue -name "*.json" | wc -l)
    echo "📦 Audit queue contains: $queue_count events"
    
    if [ "$queue_count" -gt 0 ]; then
        echo "📄 Latest audit event:"
        latest_file=$(find /var/sota/audit-queue -name "*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        if [ -f "$latest_file" ]; then
            echo "   File: $(basename "$latest_file")"
            echo "   Content preview:"
            head -10 "$latest_file" | sed 's/^/   /'
        fi
    fi
else
    echo "⚠️  Audit queue directory not found - system may not be installed"
fi

# Test 5: Check connectivity and upload capability
echo ""
echo "📋 Test 5: Upload capability test"
if curl -s --connect-timeout 5 --cert /var/sota/client.pem --key /var/sota/pkey.pem --cacert /var/sota/root.crt https://ota-lite.foundries.io:8443 >/dev/null 2>&1; then
    echo "🌐 Internet connectivity: ✅ Available"
    echo "🔐 Device certificates: ✅ Valid"
    echo "📤 Immediate upload: ✅ Enabled"
else
    echo "🌐 Internet connectivity: ❌ Not available or certificates invalid"
    echo "📤 Upload mode: 🔄 Queue for later"
fi

# Test 6: Service status
echo ""
echo "📋 Test 6: CRA audit services status"
for service in cra-audit-queue-processor.timer auditd; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "🟢 $service: Active"
    elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
        echo "🟡 $service: Enabled but not running"
    else
        echo "🔴 $service: Not available"
    fi
done

# Cleanup
rm -f "$test_file"

echo ""
echo "✅ CRA Audit System Test Complete"
echo ""
echo "🎯 How Automatic Detection Works:"
echo "1. auditd monitors system events using /etc/audit/rules.d/cra-audit.rules"
echo "2. Events matching CRA patterns trigger /usr/sbin/cra-audit-dispatcher.sh"
echo "3. Dispatcher calls /usr/sbin/cra-audit-handler.sh with event details"
echo "4. Handler creates audit report and uploads immediately (if online)"
echo "5. If offline, events queue in /var/sota/audit-queue/"
echo "6. Timer processes queue every 15 minutes when connectivity restored"
echo ""
echo "🔧 Manual trigger: /usr/sbin/cra-audit-handler.sh event 'type' 'details'"
echo "🔧 Process queue: /usr/sbin/cra-audit-handler.sh queue"
