#!/bin/bash
# Raspberry Pi Setup Script cho YOLO-CROWD
# ========================================

echo "🍓 Setting up YOLO-CROWD for Raspberry Pi 4"
echo "============================================"

# Check if running on RPi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: Not detected as Raspberry Pi"
    read -p "Continue anyway? (y/n): " continue_setup
    if [[ $continue_setup != "y" ]]; then
        exit 1
    fi
fi

# System info
echo "📋 System Information:"
echo "  - Model: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
echo "  - OS: $(lsb_release -d 2>/dev/null | cut -f2 || uname -a)"
echo "  - RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  - Storage: $(df -h / | awk 'NR==2 {print $4}') available"

# Check minimum requirements
total_mem=$(free -m | awk '/^Mem:/ {print $2}')
if [ $total_mem -lt 3500 ]; then
    echo "❌ Warning: Less than 4GB RAM detected ($total_mem MB)"
    echo "   Recommend RPi 4 with 8GB for optimal performance"
fi

echo ""
echo "🔧 RPi Optimization Setup:"

# 1. Update system
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install system dependencies
echo "2. Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    libatlas-base-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff5 \
    libffi-dev

# 3. Increase swap for compilation
echo "3. Setting up swap space..."
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 4. Install Python packages
echo "4. Installing Python packages..."
pip3 install --upgrade pip

# Install PyTorch CPU version first
pip3 install torch==1.13.1+cpu torchvision==0.14.1+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install other requirements
pip3 install -r requirements_rpi.txt

# 5. Download optimized model weights
echo "5. Downloading model weights..."
if [ ! -f "yolov5s.pt" ]; then
    python3 -c "
import torch
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
torch.save(model.state_dict(), 'yolov5s.pt')
print('Model downloaded and saved')
"
fi

# 6. GPU memory split (cho camera nếu cần)
echo "6. Optimizing GPU memory split..."
if ! grep -q "gpu_mem=64" /boot/config.txt; then
    echo "gpu_mem=64" | sudo tee -a /boot/config.txt
fi

# 7. System optimizations
echo "7. Applying system optimizations..."

# CPU governor
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Kernel parameters
if ! grep -q "vm.swappiness=10" /etc/sysctl.conf; then
    echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
fi

# 8. Create test directory
echo "8. Setting up test environment..."
mkdir -p rpi_results rpi_test rpi_benchmark

# Test installation
echo "9. Testing installation..."
python3 -c "
try:
    import torch
    import cv2
    import numpy as np
    import sklearn
    from rpi_crowd_detector import RPiCrowdDetector
    print('✅ All imports successful')
    
    # Quick test
    detector = RPiCrowdDetector()
    print('✅ RPi Crowd Detector initialized')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
"

echo ""
echo "🎯 Installation Complete!"
echo "========================"
echo ""
echo "📋 Quick Start:"
echo "  1. Test single image:"
echo "     python3 rpi_crowd_detector.py --source test_data/seq_000002.jpg --output rpi_test"
echo ""
echo "  2. Use launcher script:"
echo "     ./rpi_launcher.sh"
echo ""
echo "  3. Batch processing:"
echo "     python3 rpi_crowd_detector.py --source test_data --output rpi_results --max-images 10"
echo ""
echo "💡 Performance Tips:"
echo "  - Use --img-size 320 for faster processing"
echo "  - Monitor memory with: watch -n 1 free -h"
echo "  - Limit batch size with --max-images"
echo ""
echo "🔄 Reboot recommended to apply all optimizations:"
echo "     sudo reboot"
