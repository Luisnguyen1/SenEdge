#!/bin/bash
# RPi Performance Monitoring Script
# =================================

echo "🍓 Raspberry Pi Performance Monitor"
echo "=================================="

# Check if running on RPi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Not running on Raspberry Pi (simulated mode)"
fi

# Function to get CPU temperature
get_cpu_temp() {
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        echo "scale=1; $temp/1000" | bc 2>/dev/null || echo "N/A"
    else
        echo "N/A"
    fi
}

# Function to get CPU frequency
get_cpu_freq() {
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq ]; then
        freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
        echo "scale=0; $freq/1000" | bc 2>/dev/null || echo "N/A"
    else
        echo "N/A"
    fi
}

# Function to check throttling
check_throttling() {
    if command -v vcgencmd >/dev/null 2>&1; then
        throttled=$(vcgencmd get_throttled | cut -d= -f2)
        if [ "$throttled" = "0x0" ]; then
            echo "No throttling"
        else
            echo "THROTTLED: $throttled"
        fi
    else
        echo "N/A"
    fi
}

# Continuous monitoring mode
if [ "$1" = "--continuous" ] || [ "$1" = "-c" ]; then
    echo "Starting continuous monitoring (Press Ctrl+C to stop)..."
    echo "Time        CPU%   Temp°C  Freq MHz  Memory%   Throttle"
    echo "================================================================"
    
    while true; do
        timestamp=$(date +"%H:%M:%S")
        cpu_percent=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        temp=$(get_cpu_temp)
        freq=$(get_cpu_freq)
        mem_percent=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2*100}')
        throttle=$(check_throttling)
        
        printf "%-10s %5s%% %6s°C %8s   %6s%%   %s\n" \
               "$timestamp" "$cpu_percent" "$temp" "$freq" "$mem_percent" "$throttle"
        
        sleep 1
    done
    
else
    # Single snapshot mode
    echo ""
    echo "📊 System Status:"
    echo "================"
    
    # Basic system info
    echo "🏷️  Model: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
    echo "💾 Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2 " (" int($3/$2*100) "%)"}')"
    echo "🔥 CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "🌡️  Temperature: $(get_cpu_temp)°C"
    echo "⚡ CPU Frequency: $(get_cpu_freq) MHz"
    echo "🚫 Throttling: $(check_throttling)"
    
    # Storage info
    echo ""
    echo "💽 Storage:"
    df -h / | awk 'NR==2 {print "   Root: " $3 "/" $2 " (" $5 " used)"}'
    
    # Process info
    echo ""
    echo "🔧 Top CPU Processes:"
    ps aux --sort=-%cpu | head -6 | awk 'NR==1 {print "   " $0} NR>1 {printf "   %-10s %5s%% %s\n", $1, $3, $11}'
    
    # Memory info
    echo ""
    echo "🧠 Top Memory Processes:"
    ps aux --sort=-%mem | head -6 | awk 'NR==1 {print "   " $0} NR>1 {printf "   %-10s %5s%% %s\n", $1, $4, $11}'
    
    # GPU memory (if available)
    if command -v vcgencmd >/dev/null 2>&1; then
        echo ""
        echo "🎮 GPU Memory:"
        gpu_mem=$(vcgencmd get_mem gpu | cut -d= -f2)
        echo "   GPU: $gpu_mem"
    fi
    
    # Network info
    echo ""
    echo "🌐 Network:"
    ip route get 1.1.1.1 2>/dev/null | awk '{print "   Interface: " $5 " (Gateway: " $3 ")"}'
    
    # Temperature warnings
    temp_val=$(get_cpu_temp)
    if [ "$temp_val" != "N/A" ] && [ "$temp_val" != "" ]; then
        temp_int=$(echo "$temp_val" | cut -d. -f1)
        if [ "$temp_int" -gt 70 ]; then
            echo ""
            echo "⚠️  WARNING: High temperature ($temp_val°C)!"
            echo "   Consider adding cooling or reducing workload"
        fi
    fi
    
    echo ""
    echo "💡 Usage Examples:"
    echo "   ./monitor_performance.sh --continuous    # Continuous monitoring"
    echo "   watch -n 1 ./monitor_performance.sh      # Refresh every second"
fi

echo ""
