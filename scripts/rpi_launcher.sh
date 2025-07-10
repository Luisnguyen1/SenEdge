#!/bin/bash
# RPi Crowd Detection Launcher
# =============================

echo "🍓 Raspberry Pi Crowd Detection Setup"
echo "====================================="

# Check system
echo "📋 System Info:"
echo "  - OS: $(uname -a)"
echo "  - Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  - CPU: $(nproc) cores"
echo "  - Storage: $(df -h / | awk 'NR==2 {print $4}') free"

# Set environment variables for RPi optimization
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4
export VECLIB_MAXIMUM_THREADS=4
export NUMEXPR_NUM_THREADS=4

# Memory optimization
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

echo ""
echo "🎯 Available test modes:"
echo "1. Single image test"
echo "2. Batch processing (small)"
echo "3. Batch processing (full)"
echo "4. Performance benchmark"
echo "5. Memory stress test"

read -p "Choose mode (1-5): " mode

case $mode in
    1)
        echo "🖼️  Single Image Test"
        python3 rpi_crowd_detector.py \
            --source "test_data/seq_000002.jpg" \
            --output "rpi_test" \
            --img-size 320 \
            --conf-thres 0.3
        ;;
    2)
        echo "📁 Small Batch Test (5 images)"
        python3 rpi_crowd_detector.py \
            --source "test_data" \
            --output "rpi_batch_small" \
            --img-size 320 \
            --max-images 5
        ;;
    3)
        echo "📁 Full Batch Processing"
        python3 rpi_crowd_detector.py \
            --source "test_data" \
            --output "rpi_batch_full" \
            --img-size 320
        ;;
    4)
        echo "⏱️  Performance Benchmark"
        echo "Testing different image sizes..."
        
        for size in 224 320 416; do
            echo "Testing size: ${size}x${size}"
            python3 rpi_crowd_detector.py \
                --source "test_data/seq_000002.jpg" \
                --output "rpi_benchmark_${size}" \
                --img-size $size \
                --max-images 1
        done
        ;;
    5)
        echo "🧪 Memory Stress Test"
        python3 -c "
import psutil
import time
from rpi_crowd_detector import RPiCrowdDetector

print('Initial Memory:', psutil.virtual_memory().percent, '%')

detector = RPiCrowdDetector()
print('After model load:', psutil.virtual_memory().percent, '%')

# Process multiple images
import glob
images = glob.glob('test_data/*.jpg')[:10]

for i, img in enumerate(images):
    print(f'Processing {i+1}/10: {psutil.virtual_memory().percent:.1f}%')
    detector.detect_single_image(img, f'stress_test_{i}.jpg', visualize=False)
    time.sleep(0.5)

print('Final Memory:', psutil.virtual_memory().percent, '%')
"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✅ Processing completed!"
echo "📊 Check results in output directory"

# Show results
if [ -d "rpi_test" ] || [ -d "rpi_batch_small" ] || [ -d "rpi_batch_full" ]; then
    echo ""
    echo "📁 Generated files:"
    find . -name "rpi_*" -type d | head -3 | xargs ls -la
fi
