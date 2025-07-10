#!/usr/bin/env python3
"""
Single Image Demo for RPi4 Crowd Detection
==========================================

Simple example of processing one image with optimized settings.
"""

import sys
import os
sys.path.append('..')

from rpi_crowd_detector import RPiCrowdDetector
import time

def single_image_demo():
    """Demo xử lý 1 ảnh đơn giản"""
    
    print("🍓 RPi4 Single Image Demo")
    print("=" * 30)
    
    # Input và output paths
    input_image = "../test_data/seq_000002.jpg"
    output_path = "demo_result.jpg"
    
    if not os.path.exists(input_image):
        print(f"❌ Input image not found: {input_image}")
        print("   Make sure you're running from rpi4_model/examples/")
        return
    
    # Initialize detector với settings tối ưu cho demo
    detector = RPiCrowdDetector(
        img_size=320,        # Fast processing
        conf_thres=0.25,     # Balanced detection
    )
    
    # Adjust crowd analyzer for demo
    detector.crowd_analyzer.max_distance = 80  # Sensitive clustering
    
    print(f"\n🔍 Processing: {input_image}")
    start_time = time.time()
    
    # Process image
    result = detector.detect_single_image(
        input_image, 
        output_path, 
        visualize=True
    )
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total demo time: {total_time:.2f}s")
    
    if result:
        print(f"\n✅ Demo completed!")
        print(f"📁 Results saved: {output_path}")
        print(f"📄 Stats saved: demo_result_stats.txt")
        
        # Quick summary
        crowd_data = result['crowd_analysis']
        print(f"\n📊 Quick Summary:")
        print(f"   👥 People detected: {result['total_people']}")
        print(f"   🏃 Crowds found: {crowd_data['total_crowds']}")
        if crowd_data['crowds']:
            for crowd in crowd_data['crowds']:
                print(f"      • Crowd {crowd['id']}: {crowd['people_count']} people")
    
    else:
        print("❌ Demo failed!")

if __name__ == "__main__":
    single_image_demo()
