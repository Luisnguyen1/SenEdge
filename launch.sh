#!/bin/bash
# RPi4 Model Launcher - Set up paths correctly
# ============================================

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Set Python path to include parent directory
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

echo "🍓 RPi4 Crowd Detection Launcher"
echo "================================"
echo "🔧 Setup:"
echo "   Script dir: $SCRIPT_DIR"
echo "   Root dir: $ROOT_DIR"
echo "   Python path: $PYTHONPATH"

# Change to RPi4 model directory
cd "$SCRIPT_DIR"

# Check if we can import required modules
python3 -c "
import sys
sys.path.append('..')
try:
    from models.experimental import attempt_load
    from utils.general import check_img_size
    print('✅ Module imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
" || {
    echo "❌ Module import failed. Make sure you're running from the correct directory."
    exit 1
}

# Run the requested command or interactive menu
if [ $# -eq 0 ]; then
    echo ""
    echo "🎯 Select option:"
    echo "1. Single image demo"
    echo "2. Batch processing demo"  
    echo "3. Performance monitoring"
    echo "4. Custom command"
    
    read -p "Choose (1-4): " choice
    
    case $choice in
        1)
            echo "🖼️  Running single image demo..."
            python3 examples/single_image_demo.py
            ;;
        2)
            echo "📁 Running batch processing demo..."
            python3 examples/batch_processing.py
            ;;
        3)
            echo "📊 Starting performance monitor..."
            ./scripts/monitor_performance.sh
            ;;
        4)
            echo "Enter custom command (e.g., python3 rpi_crowd_detector.py --help):"
            read -p "Command: " custom_cmd
            eval $custom_cmd
            ;;
        *)
            echo "❌ Invalid option"
            exit 1
            ;;
    esac
else
    # Execute provided command
    echo "🚀 Executing: $@"
    eval "$@"
fi
