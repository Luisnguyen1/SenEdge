#!/usr/bin/env python3
"""
Batch Processing Demo for RPi4
==============================

Example of processing multiple images with memory management.
"""

import sys
import os
import time
import psutil
sys.path.append('..')

from rpi_crowd_detector import RPiCrowdDetector
from pathlib import Path

def batch_processing_demo():
    """Demo xử lý batch với memory management"""
    
    print("🍓 RPi4 Batch Processing Demo")
    print("=" * 35)
    
    # Paths
    input_folder = "../test_data"
    output_folder = "batch_results"
    
    if not os.path.exists(input_folder):
        print(f"❌ Input folder not found: {input_folder}")
        return
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Initialize detector
    detector = RPiCrowdDetector(
        img_size=320,
        conf_thres=0.3
    )
    
    # Find images
    img_formats = ['.jpg', '.jpeg', '.png']
    image_files = []
    for ext in img_formats:
        image_files.extend(Path(input_folder).glob(f'*{ext}'))
        image_files.extend(Path(input_folder).glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"❌ No images found in {input_folder}")
        return
    
    # Limit for demo (RPi memory management)
    max_images = min(len(image_files), 5)  # Process max 5 images
    image_files = image_files[:max_images]
    
    print(f"📁 Found {len(image_files)} images to process")
    print(f"💾 Initial memory: {psutil.virtual_memory().percent:.1f}%")
    
    # Process images
    results = []
    total_people = 0
    total_crowds = 0
    
    for i, img_path in enumerate(image_files, 1):
        print(f"\n[{i}/{max_images}] Processing: {img_path.name}")
        
        # Memory check
        mem_percent = psutil.virtual_memory().percent
        print(f"   💾 Memory: {mem_percent:.1f}%")
        
        if mem_percent > 85:
            print("   ⚠️  High memory usage - pausing...")
            time.sleep(2)
        
        # Process image
        output_path = os.path.join(output_folder, f"result_{img_path.name}")
        
        try:
            start_time = time.time()
            result = detector.detect_single_image(str(img_path), output_path)
            process_time = time.time() - start_time
            
            if result:
                results.append(result)
                crowd_data = result['crowd_analysis']
                people_count = result['total_people']
                crowds_count = crowd_data['total_crowds']
                
                total_people += people_count
                total_crowds += crowds_count
                
                print(f"   ⏱️  Time: {process_time:.2f}s")
                print(f"   👥 People: {people_count}, Crowds: {crowds_count}")
            else:
                print("   ❌ Processing failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Memory cleanup every 2 images
        if i % 2 == 0:
            import gc
            gc.collect()
    
    # Final summary
    print(f"\n📊 BATCH PROCESSING SUMMARY:")
    print("=" * 40)
    print(f"✅ Images processed: {len(results)}/{max_images}")
    print(f"👥 Total people detected: {total_people}")
    print(f"🏃 Total crowds detected: {total_crowds}")
    print(f"💾 Final memory: {psutil.virtual_memory().percent:.1f}%")
    print(f"📁 Results saved in: {output_folder}/")
    
    # Average stats
    if results:
        avg_people = total_people / len(results)
        avg_crowds = total_crowds / len(results)
        print(f"\n📈 Averages per image:")
        print(f"   👥 People: {avg_people:.1f}")
        print(f"   🏃 Crowds: {avg_crowds:.1f}")
    
    # Performance tips
    print(f"\n💡 Performance Tips:")
    print(f"   • Use --max-images to limit batch size")
    print(f"   • Monitor memory with: watch -n 1 free -h")
    print(f"   • Add cooling for sustained processing")

if __name__ == "__main__":
    batch_processing_demo()
