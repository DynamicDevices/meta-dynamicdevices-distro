#!/bin/bash
# PM Analyzer Alternative for i.MX93 Jaguar E-Ink Board
# Lightweight power management analyzer when full tools aren't available

set -e

SCRIPT_NAME="pm-analyzer"
LOG_FILE="/tmp/pm-analyzer-${HOSTNAME}-$(date +%Y%m%d_%H%M%S).log"

# Simple logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $*" | tee -a "$LOG_FILE"
}

analyze_suspend_resume() {
    log "=== Suspend/Resume Analysis ==="
    
    # Check suspend capabilities
    if [ -f /sys/power/state ]; then
        log "Available suspend states: $(cat /sys/power/state)"
    fi
    
    if [ -f /sys/power/mem_sleep ]; then
        log "Available memory sleep modes: $(cat /sys/power/mem_sleep)"
    fi
    
    # Check wakeup sources
    if [ -f /sys/power/wakeup_count ]; then
        log "Current wakeup count: $(cat /sys/power/wakeup_count)"
    fi
    
    log "Active wakeup sources:"
    if [ -d /sys/class/wakeup ]; then
        for ws in /sys/class/wakeup/wakeup*; do
            if [ -f "$ws/active_count" ] && [ -f "$ws/name" ]; then
                name=$(cat "$ws/name")
                count=$(cat "$ws/active_count")
                if [ "$count" -gt 0 ]; then
                    log "  $name: $count activations"
                fi
            fi
        done
    fi
}

analyze_power_consumption() {
    log "=== Power Consumption Estimates ==="
    
    # CPU usage
    if [ -f /proc/stat ]; then
        cpu_line=$(head -1 /proc/stat)
        log "CPU stats: $cpu_line"
    fi
    
    # Memory usage
    if [ -f /proc/meminfo ]; then
        mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        mem_free=$(grep MemFree /proc/meminfo | awk '{print $2}')
        mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        log "Memory: Total=${mem_total}kB, Free=${mem_free}kB, Available=${mem_available}kB"
    fi
    
    # Load average
    if [ -f /proc/loadavg ]; then
        load=$(cat /proc/loadavg)
        log "Load average: $load"
    fi
}

analyze_frequency_scaling() {
    log "=== Frequency Scaling Analysis ==="
    
    # Check for standard CPUFreq
    if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq; do
            if [ -d "$cpu" ]; then
                cpu_num=$(basename "$(dirname "$cpu")")
                cur_freq=$(cat "$cpu/scaling_cur_freq" 2>/dev/null || echo "unknown")
                governor=$(cat "$cpu/scaling_governor" 2>/dev/null || echo "unknown")
                log "$cpu_num: ${cur_freq}kHz, governor: $governor"
            fi
        done
    fi
    
    # Check for i.MX93 LPM driver
    if [ -d /sys/devices/platform/imx93-lpm ]; then
        mode=$(cat /sys/devices/platform/imx93-lpm/mode 2>/dev/null || echo "unknown")
        available=$(cat /sys/devices/platform/imx93-lpm/available_modes 2>/dev/null || echo "unknown")
        log "i.MX93 LPM: mode=$mode, available=$available"
    fi
    
    # Check DEVFREQ (for DDR/bus scaling)
    if [ -d /sys/class/devfreq ]; then
        for dev in /sys/class/devfreq/*; do
            if [ -d "$dev" ]; then
                name=$(basename "$dev")
                cur_freq=$(cat "$dev/cur_freq" 2>/dev/null || echo "unknown")
                governor=$(cat "$dev/governor" 2>/dev/null || echo "unknown")
                log "DEVFREQ $name: ${cur_freq}Hz, governor: $governor"
            fi
        done
    fi
}

analyze_runtime_pm() {
    log "=== Runtime Power Management Analysis ==="
    
    # Key device categories for i.MX93
    local device_patterns=(
        "mmc:MMC/SDIO"
        "spi:SPI"
        "i2c:I2C"
        "uart:UART"
        "usb:USB"
        "gpio:GPIO"
    )
    
    for pattern in "${device_patterns[@]}"; do
        device_type=$(echo "$pattern" | cut -d: -f1)
        desc=$(echo "$pattern" | cut -d: -f2)
        
        log "$desc devices:"
        find /sys/devices -name "*${device_type}*" -type d 2>/dev/null | while read -r device_path; do
            if [ -f "$device_path/power/runtime_status" ]; then
                status=$(cat "$device_path/power/runtime_status")
                control=$(cat "$device_path/power/control" 2>/dev/null || echo "unknown")
                device_name=$(basename "$device_path")
                log "  $device_name: $status (control: $control)"
            fi
        done
    done
}

test_power_transitions() {
    log "=== Power Transition Tests ==="
    
    # Test CPU frequency changes (if available)
    if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
        available_freqs=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies 2>/dev/null)
        if [ -n "$available_freqs" ]; then
            log "Testing CPU frequency transitions..."
            for freq in $available_freqs; do
                if echo "$freq" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_setspeed 2>/dev/null; then
                    actual_freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
                    log "  Set $freq kHz, actual: $actual_freq kHz"
                    sleep 1
                fi
            done
        fi
    fi
    
    # Test i.MX93 LPM mode changes (if available)
    if [ -f /sys/devices/platform/imx93-lpm/available_modes ]; then
        available_modes=$(cat /sys/devices/platform/imx93-lpm/available_modes 2>/dev/null)
        if [ -n "$available_modes" ]; then
            log "Testing i.MX93 LPM mode transitions..."
            current_mode=$(cat /sys/devices/platform/imx93-lpm/mode)
            for mode in $available_modes; do
                if echo "$mode" > /sys/devices/platform/imx93-lpm/mode 2>/dev/null; then
                    actual_mode=$(cat /sys/devices/platform/imx93-lpm/mode)
                    log "  Set mode $mode, actual: $actual_mode"
                    sleep 2
                fi
            done
            # Restore original mode
            echo "$current_mode" > /sys/devices/platform/imx93-lpm/mode 2>/dev/null || true
        fi
    fi
}

generate_report() {
    log "=== Power Management Report Generated ==="
    log "Report saved to: $LOG_FILE"
    log "System: $(uname -a)"
    log "Uptime: $(uptime)"
    
    # Copy to a standard location
    cp "$LOG_FILE" "/tmp/pm-analyzer-latest.log"
    log "Latest report also available at: /tmp/pm-analyzer-latest.log"
}

show_usage() {
    echo "PM Analyzer - Lightweight power management analyzer for i.MX93"
    echo ""
    echo "Usage: $SCRIPT_NAME [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --all           Run all power management analyses"
    echo "  -s, --suspend       Analyze suspend/resume capabilities"
    echo "  -c, --consumption   Analyze current power consumption"
    echo "  -f, --frequency     Analyze frequency scaling"
    echo "  -r, --runtime       Analyze runtime power management"
    echo "  -t, --test          Test power transitions (may affect system)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $SCRIPT_NAME --all                # Complete analysis"
    echo "  $SCRIPT_NAME --frequency --runtime # Specific analyses"
    echo ""
}

# Main script logic
main() {
    case "${1:-}" in
        -a|--all)
            log "Starting comprehensive power management analysis..."
            analyze_suspend_resume
            analyze_power_consumption
            analyze_frequency_scaling
            analyze_runtime_pm
            generate_report
            ;;
        -s|--suspend)
            analyze_suspend_resume
            generate_report
            ;;
        -c|--consumption)
            analyze_power_consumption
            generate_report
            ;;
        -f|--frequency)
            analyze_frequency_scaling
            generate_report
            ;;
        -r|--runtime)
            analyze_runtime_pm
            generate_report
            ;;
        -t|--test)
            log "WARNING: This will test power transitions and may affect system performance"
            read -p "Continue? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                test_power_transitions
                generate_report
            else
                log "Test cancelled by user"
            fi
            ;;
        -h|--help|"")
            show_usage
            ;;
        *)
            echo "ERROR: Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
