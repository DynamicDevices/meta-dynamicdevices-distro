#!/bin/bash
# Power Analysis Suite for i.MX93 Jaguar E-Ink Board
# Comprehensive power monitoring and analysis tools for development builds

set -e

SCRIPT_NAME="power-analysis-suite"
LOG_DIR="/tmp/power-analysis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  i.MX93 Jaguar E-Ink Power Analysis Suite${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_section() {
    echo -e "${GREEN}=== $1 ===${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

check_tools() {
    print_section "Checking Available Power Monitoring Tools"
    
    local tools=(
        "powertop:PowerTOP - Power consumption analyzer"
        "iotop:IOTop - I/O monitoring"
        "htop:HTop - Process monitoring"
        "perf:Perf - Performance analysis"
        "trace-cmd:Trace-cmd - Kernel tracing"
        "iw:IW - Wireless tools"
        "i2cdetect:I2C Tools - Hardware monitoring"
        "cpufreq-info:CPUFreq Utils - CPU frequency monitoring"
    )
    
    for tool_info in "${tools[@]}"; do
        tool=$(echo "$tool_info" | cut -d: -f1)
        desc=$(echo "$tool_info" | cut -d: -f2)
        
        if command -v "$tool" >/dev/null 2>&1; then
            echo -e "  ✓ ${GREEN}${tool}${NC} - $desc"
        else
            echo -e "  ✗ ${RED}${tool}${NC} - $desc (not available)"
        fi
    done
    echo ""
}

analyze_cpu_power() {
    print_section "CPU Power Management Analysis"
    
    echo "Current CPU frequency and governor settings:"
    if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
        echo "  Governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo 'N/A')"
        echo "  Current frequency: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null || echo 'N/A') kHz"
        echo "  Available frequencies: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies 2>/dev/null || echo 'N/A')"
        echo "  Available governors: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors 2>/dev/null || echo 'N/A')"
    else
        print_warning "CPUFreq interface not available - checking i.MX93 LPM driver"
        if [ -d /sys/devices/platform/imx93-lpm ]; then
            echo "  i.MX93 LPM Mode: $(cat /sys/devices/platform/imx93-lpm/mode 2>/dev/null || echo 'N/A')"
            echo "  Available modes: $(cat /sys/devices/platform/imx93-lpm/available_modes 2>/dev/null || echo 'N/A')"
        else
            print_error "Neither CPUFreq nor i.MX93 LPM driver found"
        fi
    fi
    
    echo ""
    echo "CPU idle states:"
    if [ -d /sys/devices/system/cpu/cpu0/cpuidle ]; then
        for state in /sys/devices/system/cpu/cpu0/cpuidle/state*; do
            if [ -d "$state" ]; then
                name=$(cat "$state/name" 2>/dev/null || echo "unknown")
                desc=$(cat "$state/desc" 2>/dev/null || echo "no description")
                time=$(cat "$state/time" 2>/dev/null || echo "0")
                usage=$(cat "$state/usage" 2>/dev/null || echo "0")
                echo "  $(basename "$state"): $name - $desc (time: ${time}us, usage: $usage)"
            fi
        done
    else
        print_warning "CPU idle states not available"
    fi
    echo ""
}

analyze_thermal() {
    print_section "Thermal and Temperature Analysis"
    
    echo "Current temperatures:"
    if command -v sensors >/dev/null 2>&1; then
        sensors 2>/dev/null || echo "  No sensors detected"
    else
        # Fallback to thermal zones
        for zone in /sys/class/thermal/thermal_zone*; do
            if [ -d "$zone" ]; then
                type=$(cat "$zone/type" 2>/dev/null || echo "unknown")
                temp=$(cat "$zone/temp" 2>/dev/null || echo "0")
                temp_c=$((temp / 1000))
                echo "  $type: ${temp_c}°C"
            fi
        done
    fi
    
    echo ""
    echo "Thermal governors:"
    for zone in /sys/class/thermal/thermal_zone*; do
        if [ -d "$zone" ]; then
            type=$(cat "$zone/type" 2>/dev/null || echo "unknown")
            policy=$(cat "$zone/policy" 2>/dev/null || echo "none")
            echo "  $type: $policy"
        fi
    done
    echo ""
}

analyze_power_domains() {
    print_section "Power Domain Analysis"
    
    echo "Power domains status:"
    if [ -d /sys/kernel/debug/pm_genpd ]; then
        echo "  Generic power domains:"
        cat /sys/kernel/debug/pm_genpd/pm_genpd_summary 2>/dev/null || echo "  Not available (debugfs may not be mounted)"
    else
        print_warning "Power domain debug info not available"
    fi
    
    echo ""
    echo "Runtime PM status for key devices:"
    local devices=(
        "/sys/devices/platform/44000000.mmc"  # eMMC
        "/sys/devices/platform/42850000.mmc"  # SDIO WiFi
        "/sys/devices/platform/44320000.spi"  # SPI
        "/sys/devices/platform/44340000.i2c"  # I2C
    )
    
    for device in "${devices[@]}"; do
        if [ -d "$device/power" ]; then
            runtime_status=$(cat "$device/power/runtime_status" 2>/dev/null || echo "unknown")
            control=$(cat "$device/power/control" 2>/dev/null || echo "unknown")
            echo "  $(basename "$device"): $runtime_status (control: $control)"
        fi
    done
    echo ""
}

analyze_wireless_power() {
    print_section "Wireless Power Management Analysis"
    
    echo "WiFi power management:"
    if command -v iw >/dev/null 2>&1; then
        for dev in /sys/class/net/wlan*; do
            if [ -d "$dev" ]; then
                interface=$(basename "$dev")
                echo "  Interface: $interface"
                iw dev "$interface" get power_save 2>/dev/null || echo "    Power save info not available"
                
                # Check if interface is up
                if [ -f "$dev/operstate" ]; then
                    state=$(cat "$dev/operstate")
                    echo "    State: $state"
                fi
            fi
        done
    else
        print_warning "iw tool not available for WiFi power analysis"
    fi
    
    echo ""
    echo "Bluetooth power management:"
    if [ -d /sys/class/bluetooth ]; then
        for hci in /sys/class/bluetooth/hci*; do
            if [ -d "$hci" ]; then
                echo "  $(basename "$hci"): $(cat "$hci/power/runtime_status" 2>/dev/null || echo 'unknown')"
            fi
        done
    else
        echo "  No Bluetooth devices found"
    fi
    echo ""
}

run_powertop_analysis() {
    print_section "PowerTOP Analysis"
    
    if command -v powertop >/dev/null 2>&1; then
        echo "Running PowerTOP analysis (this may take a few seconds)..."
        mkdir -p "$LOG_DIR"
        
        # Run powertop in non-interactive mode
        timeout 30 powertop --auto-tune >/dev/null 2>&1 || true
        powertop --html="$LOG_DIR/powertop_${TIMESTAMP}.html" --time=10 >/dev/null 2>&1 || true
        
        echo "  PowerTOP report saved to: $LOG_DIR/powertop_${TIMESTAMP}.html"
        
        # Quick summary
        powertop --csv="$LOG_DIR/powertop_${TIMESTAMP}.csv" --time=5 >/dev/null 2>&1 || true
        if [ -f "$LOG_DIR/powertop_${TIMESTAMP}.csv" ]; then
            echo "  PowerTOP CSV data saved to: $LOG_DIR/powertop_${TIMESTAMP}.csv"
        fi
    else
        print_warning "PowerTOP not available"
    fi
    echo ""
}

show_usage() {
    print_header
    echo "Usage: $SCRIPT_NAME [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --all           Run all power analysis tests"
    echo "  -c, --cpu           Analyze CPU power management"
    echo "  -t, --thermal       Analyze thermal management"
    echo "  -p, --powertop      Run PowerTOP analysis"
    echo "  -w, --wireless      Analyze wireless power management"
    echo "  -d, --domains       Analyze power domains"
    echo "  -s, --summary       Show quick power summary"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $SCRIPT_NAME --all                # Run complete power analysis"
    echo "  $SCRIPT_NAME --cpu --thermal      # Analyze CPU and thermal only"
    echo "  $SCRIPT_NAME --summary            # Quick power status summary"
    echo ""
}

quick_summary() {
    print_section "Quick Power Status Summary"
    
    # CPU frequency
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq ]; then
        freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
        gov=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
        echo "  CPU: ${freq} kHz, Governor: $gov"
    elif [ -f /sys/devices/platform/imx93-lpm/mode ]; then
        mode=$(cat /sys/devices/platform/imx93-lpm/mode)
        echo "  i.MX93 LPM Mode: $mode"
    fi
    
    # Temperature
    temp_found=false
    for zone in /sys/class/thermal/thermal_zone*; do
        if [ -f "$zone/temp" ]; then
            type=$(cat "$zone/type" 2>/dev/null || echo "cpu")
            temp=$(cat "$zone/temp")
            temp_c=$((temp / 1000))
            echo "  Temperature ($type): ${temp_c}°C"
            temp_found=true
            break
        fi
    done
    [ "$temp_found" = false ] && echo "  Temperature: Not available"
    
    # WiFi status
    if [ -d /sys/class/net/wlan0 ]; then
        state=$(cat /sys/class/net/wlan0/operstate 2>/dev/null || echo "unknown")
        echo "  WiFi: $state"
    fi
    
    # Load average
    if [ -f /proc/loadavg ]; then
        load=$(cut -d' ' -f1-3 /proc/loadavg)
        echo "  Load average: $load"
    fi
    
    echo ""
}

# Main script logic
main() {
    mkdir -p "$LOG_DIR"
    
    case "${1:-}" in
        -a|--all)
            print_header
            check_tools
            analyze_cpu_power
            analyze_thermal
            analyze_power_domains
            analyze_wireless_power
            run_powertop_analysis
            ;;
        -c|--cpu)
            print_header
            analyze_cpu_power
            ;;
        -t|--thermal)
            print_header
            analyze_thermal
            ;;
        -p|--powertop)
            print_header
            run_powertop_analysis
            ;;
        -w|--wireless)
            print_header
            analyze_wireless_power
            ;;
        -d|--domains)
            print_header
            analyze_power_domains
            ;;
        -s|--summary)
            print_header
            quick_summary
            ;;
        -h|--help|"")
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
