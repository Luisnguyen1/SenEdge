#!/usr/bin/env python3
"""
Raspberry Pi Optimized Crowd Detection
=====================================

Tối ưu hóa YOLO-CROWD cho Raspberry Pi 4:
- Giảm memory usage
- Tăng processing speed
- Lightweight crowd analysis
- Optimized visualization
"""

import argparse
import os
import sys
import cv2
import torch
import time
from pathlib import Path
import numpy as np
import psutil

# Add current directory to path
sys.path.append('.')
sys.path.append('..')  # For accessing parent directory modules

from models.experimental import attempt_load
from utils.datasets import LoadImages
from utils.general import check_img_size, non_max_suppression, scale_coords
from utils.plots import plot_one_box
from utils.torch_utils import select_device
from sklearn.cluster import DBSCAN


class LiteCrowdAnalyzer:
    """Lightweight crowd analyzer tối ưu cho Raspberry Pi"""
    
    def __init__(self, min_people=4, max_distance=60):
        self.min_people = min_people
        self.max_distance = max_distance
    
    def extract_person_centers(self, detections):
        """Trích xuất center points của người"""
        centers = []
        for det in detections:
            if det['class'] == 'person':
                bbox = det['bbox']
                cx = (bbox[0] + bbox[2]) // 2
                cy = (bbox[1] + bbox[3]) // 2
                centers.append([cx, cy])
        return np.array(centers) if centers else np.array([]).reshape(0, 2)
    
    def cluster_crowds_lite(self, person_centers):
        """Fast clustering chỉ dùng DBSCAN"""
        if len(person_centers) < self.min_people:
            return {
                'crowds': [],
                'isolated_people': len(person_centers),
                'total_crowds': 0,
                'total_people_in_crowds': 0
            }
        
        # DBSCAN clustering
        clustering = DBSCAN(eps=self.max_distance, min_samples=self.min_people)
        labels = clustering.fit_predict(person_centers)
        
        crowds = []
        isolated_count = 0
        
        # Process clusters
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:  # Noise points
                isolated_count = int(np.sum(labels == -1))
            else:
                cluster_mask = labels == label
                cluster_points = person_centers[cluster_mask]
                
                if len(cluster_points) >= self.min_people:
                    center = np.mean(cluster_points, axis=0)
                    
                    # Simple bounding box
                    min_x, min_y = np.min(cluster_points, axis=0)
                    max_x, max_y = np.max(cluster_points, axis=0)
                    
                    crowd_info = {
                        'id': int(label),  # Convert numpy int to Python int
                        'people_count': int(len(cluster_points)),
                        'center': [float(center[0]), float(center[1])],  # Convert to Python float
                        'bbox': [int(min_x), int(min_y), int(max_x), int(max_y)],
                        'size': [int(max_x - min_x), int(max_y - min_y)]
                    }
                    crowds.append(crowd_info)
        
        return {
            'crowds': crowds,
            'isolated_people': int(isolated_count),  # Convert to Python int
            'total_crowds': int(len(crowds)),
            'total_people_in_crowds': int(sum(c['people_count'] for c in crowds))
        }


class RPiCrowdDetector:
    """Optimized crowd detector cho Raspberry Pi 4"""
    
    def __init__(self, weights='yolov5s.pt', img_size=320, conf_thres=0.3, iou_thres=0.5):
        """
        Initialize với settings tối ưu cho RPi
        """
        self.weights = weights
        self.img_size = img_size  # Giảm từ 416 → 320
        self.conf_thres = conf_thres  # Tăng threshold để giảm false positives
        self.iou_thres = iou_thres
        
        print("Khởi tạo RPi Crowd Detector...")
        self._print_system_info()
        
        # Initialize device and model variables
        self.device = None
        self.model = None
        self.stride = None
        self.names = None
        
        # Load model với optimizations
        self._load_optimized_model()
        
        # Lightweight crowd analyzer
        self.crowd_analyzer = LiteCrowdAnalyzer(min_people=4, max_distance=50)
        
        print("RPi Crowd Detector sẵn sàng!")
    
    def _print_system_info(self):
        """In thông tin hệ thống RPi"""
        try:
            memory = psutil.virtual_memory()
            print(f"RAM: {memory.total/1024**3:.1f}GB total, {memory.available/1024**3:.1f}GB available")
            print(f"CPU cores: {psutil.cpu_count()}")
            print(f"CPU usage: {psutil.cpu_percent()}%")
        except:
            print("System info không available")
    
    def _load_optimized_model(self):
        """Load model với optimizations cho RPi"""
        try:
            print(f"Loading model: {self.weights}")
            
            # Skip legacy attempt_load, go straight to ultralytics
            raise Exception("Bypassing legacy model loading for RPi optimization")
            
        except Exception as e:
            print(f"Primary model loading error: {e}")
            # Direct ultralytics loading for RPi4 optimization
            try:
                print("Trying final fallback - loading minimal YOLOv5...")
                import ultralytics
                from ultralytics import YOLO
                
                # Use object detection model, not classification
                if 'cls' in self.weights or 'classify' in self.weights:
                    # If accidentally using classification model, switch to detection
                    self.weights = self.weights.replace('-cls', '').replace('cls', '')
                    if not self.weights.endswith('.pt'):
                        self.weights += '.pt'
                    print(f"🔄 Switched to detection model: {self.weights}")
                
                self.model = YOLO(self.weights)
                self.device = 'cpu'  # Force CPU for RPi4
                self.names = self.model.names
                self.stride = 32
                print("✅ Ultralytics YOLO model loaded")
                
            except Exception as e2:
                print(f"Ultralytics model loading error: {e2}")
                # Final fallback: try torch hub with correct detection model
                try:
                    print("Trying torch hub with detection model...")
                    import torch
                    torch.hub._validate_not_a_forked_repo = lambda a, b, c: True
                    self.model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True, trust_repo=True)
                    self.device = 'cpu'
                    self.model.eval()
                    self.names = self.model.names
                    self.stride = 32
                    print("✅ Torch hub YOLOv5 detection model loaded")
                    
                except Exception as e3:
                    print(f"All model loading attempts failed. Final error: {e3}")
                    raise Exception(f"Could not load any model. Errors: Primary: {e}, Ultralytics: {e2}, Hub: {e3}")
    
    def detect_single_image(self, image_path, save_path=None, visualize=True):
        """
        Phát hiện crowd trong 1 ảnh với tối ưu hóa RPi
        """
        if not os.path.exists(image_path):
            print(f"File không tồn tại: {image_path}")
            return None
        
        print(f"🔍 Analyzing: {Path(image_path).name}")
        start_time = time.time()
        
        # Load và resize ảnh
        original_img = cv2.imread(image_path)
        if original_img is None:
            print(f"Không thể đọc ảnh: {image_path}")
            return None
        
        # Resize để giảm processing time
        height, width = original_img.shape[:2]
        if max(height, width) > 800:  # Resize nếu quá lớn
            scale = 800 / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(original_img, (new_width, new_height))
            scale_factor = scale
        else:
            img = original_img.copy()
            scale_factor = 1.0
        
        # Run inference based on model type
        inference_start = time.time()
        detections = []
        
        try:
            # Check if this is ultralytics YOLO model
            if hasattr(self.model, 'predict'):
                # Ultralytics YOLO model
                results = self.model.predict(img, conf=self.conf_thres, iou=self.iou_thres, classes=[0], verbose=False)
                inference_time = time.time() - inference_start
                
                # Extract detections from ultralytics results
                if len(results) > 0 and hasattr(results[0], 'boxes') and len(results[0].boxes) > 0:
                    boxes = results[0].boxes
                    for i in range(len(boxes)):
                        if int(boxes.cls[i]) == 0:  # Person class
                            x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                            conf = float(boxes.conf[i])
                            
                            # Scale back to original image if needed
                            if scale_factor != 1.0:
                                x1, y1, x2, y2 = [coord / scale_factor for coord in [x1, y1, x2, y2]]
                            
                            detections.append({
                                'class': 'person',
                                'confidence': float(conf),
                                'bbox': [int(float(x1)), int(float(y1)), int(float(x2)), int(float(y2))]
                            })
                            
            else:
                # Traditional YOLOv5 model (torch hub or attempt_load)
                img_tensor = self._prepare_image(img)
                
                with torch.no_grad():
                    pred = self.model(img_tensor)
                    if isinstance(pred, tuple):
                        pred = pred[0]
                    if not isinstance(pred, torch.Tensor):
                        pred = pred[0] if isinstance(pred, list) else pred
                        
                inference_time = time.time() - inference_start
                
                # Post-processing
                pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=[0])  # Only person class
                
                # Extract detections
                if len(pred) > 0 and len(pred[0]) > 0:
                    det = pred[0]
                    # Scale back to resized image coordinates
                    det[:, :4] = scale_coords(img_tensor.shape[2:], det[:, :4], img.shape).round()
                    
                    for *xyxy, conf, cls in det:
                        if int(cls) == 0:  # Person class only
                            # Scale back to original image if needed
                            if scale_factor != 1.0:
                                xyxy = [coord / scale_factor for coord in xyxy]
                            
                            detections.append({
                                'class': 'person',
                                'confidence': float(conf),
                                'bbox': [int(float(x)) for x in xyxy]
                            })
                            
        except Exception as e:
            print(f"Inference error: {e}")
            inference_time = time.time() - inference_start
        
        # Crowd analysis
        person_centers = self.crowd_analyzer.extract_person_centers(detections)
        crowd_results = self.crowd_analyzer.cluster_crowds_lite(person_centers)
        
        total_time = time.time() - start_time
        
        # Results
        result_data = {
            'image_path': str(image_path),
            'processing_time': f'{total_time:.2f}s',
            'inference_time': f'{inference_time:.3f}s',
            'total_people': int(len(person_centers)),
            'crowd_analysis': crowd_results,
            'scale_factor': float(scale_factor)
        }
        
        # Visualization và save
        if visualize and save_path:
            vis_img = self._create_visualization(original_img, detections, crowd_results)
            
            # Save results
            output_dir = Path(save_path).parent
            base_name = Path(save_path).stem
            
            cv2.imwrite(str(output_dir / f"{base_name}_rpi_result.jpg"), vis_img)
            
            # Save simple stats
            self._save_results_txt(result_data, str(output_dir / f"{base_name}_stats.txt"))
        
        # Print summary
        self._print_simple_summary(result_data)
        
        return result_data
    
    def _prepare_image(self, img):
        """Chuẩn bị ảnh cho model"""
        # Resize to model input size
        img_resized = cv2.resize(img, (self.img_size, self.img_size))
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        
        # Normalize
        img_norm = img_rgb.astype(np.float32) / 255.0
        
        # HWC to CHW
        img_tensor = torch.from_numpy(img_norm.transpose(2, 0, 1)).unsqueeze(0)
        
        return img_tensor.to(self.device)
    
    def _create_visualization(self, image, detections, crowd_results):
        """Tạo visualization đơn giản"""
        vis_img = image.copy()
        
        # Draw individual people (green)
        for det in detections:
            bbox = det['bbox']
            conf = det['confidence']
            cv2.rectangle(vis_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            cv2.putText(vis_img, f'{conf:.2f}', (bbox[0], bbox[1]-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw crowds (red)
        for crowd in crowd_results['crowds']:
            bbox = crowd['bbox']
            center = crowd['center']
            count = crowd['people_count']
            
            # Crowd bounding box
            cv2.rectangle(vis_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 3)
            
            # Crowd center
            cv2.circle(vis_img, (int(center[0]), int(center[1])), 8, (0, 0, 255), -1)
            
            # Crowd label
            label = f'Crowd: {count} people'
            cv2.putText(vis_img, label, (bbox[0], bbox[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Stats overlay
        stats_text = [
            f"Total: {crowd_results['total_people_in_crowds'] + crowd_results['isolated_people']} people",
            f"Crowds: {crowd_results['total_crowds']}",
            f"In crowds: {crowd_results['total_people_in_crowds']}",
            f"Isolated: {crowd_results['isolated_people']}"
        ]
        
        for i, text in enumerate(stats_text):
            y = 30 + i * 25
            cv2.putText(vis_img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(vis_img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        return vis_img
    
    def _save_results_txt(self, result_data, save_path):
        """Lưu kết quả text đơn giản"""
        with open(save_path, 'w') as f:
            f.write("RPi Crowd Detection Results\n")
            f.write("=" * 30 + "\n")
            f.write(f"Image: {result_data['image_path']}\n")
            f.write(f"Processing time: {result_data['processing_time']}\n")
            f.write(f"Inference time: {result_data['inference_time']}\n")
            f.write(f"Total people: {result_data['total_people']}\n\n")
            
            crowd_analysis = result_data['crowd_analysis']
            f.write(f"Crowds detected: {crowd_analysis['total_crowds']}\n")
            f.write(f"People in crowds: {crowd_analysis['total_people_in_crowds']}\n")
            f.write(f"Isolated people: {crowd_analysis['isolated_people']}\n\n")
            
            for i, crowd in enumerate(crowd_analysis['crowds']):
                f.write(f"Crowd {i+1}:\n")
                f.write(f"  - People: {crowd['people_count']}\n")
                f.write(f"  - Center: ({crowd['center'][0]:.0f}, {crowd['center'][1]:.0f})\n")
                f.write(f"  - Size: {crowd['size'][0]}x{crowd['size'][1]}\n\n")
    
    def _print_simple_summary(self, result_data):
        """In summary đơn giản"""
        print(f"\nPi CROWD ANALYSIS RESULTS:")
        print("=" * 40)
        
        crowd_analysis = result_data['crowd_analysis']
        print(f"Processing: {result_data['processing_time']}")
        print(f"Inference: {result_data['inference_time']}")
        print(f"Total people: {result_data['total_people']}")
        print(f"Crowds: {crowd_analysis['total_crowds']}")
        print(f"In crowds: {crowd_analysis['total_people_in_crowds']}")
        print(f"Isolated: {crowd_analysis['isolated_people']}")
        
        for crowd in crowd_analysis['crowds']:
            print(f"  • Crowd {crowd['id']}: {crowd['people_count']} people")
    
    def batch_process(self, source_dir, output_dir, max_images=None):
        """Xử lý batch với memory management"""
        if not os.path.exists(source_dir):
            print(f"Source directory không tồn tại: {source_dir}")
            return
        
        # Find images
        img_formats = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        for ext in img_formats:
            image_files.extend(Path(source_dir).glob(f'*{ext}'))
            image_files.extend(Path(source_dir).glob(f'*{ext.upper()}'))
        
        if not image_files:
            print(f"Không tìm thấy ảnh trong: {source_dir}")
            return
        
        if max_images:
            image_files = image_files[:max_images]
        
        print(f"Processing {len(image_files)} images...")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process with memory monitoring
        for i, img_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] {img_path.name}")
            
            # Memory check
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                print(f"High memory usage: {memory.percent:.1f}% - Pausing...")
                time.sleep(2)
            
            output_path = os.path.join(output_dir, f"result_{img_path.name}")
            
            try:
                result = self.detect_single_image(str(img_path), output_path, visualize=True)
                
                # Clear cache periodically
                if i % 5 == 0:
                    torch.cuda.empty_cache() if torch.cuda.is_available() else None
                    
            except Exception as e:
                print(f"Error processing {img_path.name}: {e}")
                continue
        
        print(f"\nBatch processing completed! Results in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='RPi Optimized Crowd Detection')
    parser.add_argument('--source', type=str, required=True,
                       help='Đường dẫn ảnh hoặc folder')
    parser.add_argument('--weights', type=str, default='yolov5s.pt',
                       help='Model weights path')
    parser.add_argument('--img-size', type=int, default=320,
                       help='Input image size (default: 320 for RPi)')
    parser.add_argument('--conf-thres', type=float, default=0.3,
                       help='Confidence threshold')
    parser.add_argument('--output', type=str, default='rpi_results',
                       help='Output directory')
    parser.add_argument('--max-images', type=int, default=None,
                       help='Max images to process (for testing)')
    parser.add_argument('--no-vis', action='store_true',
                       help='Skip visualization')
    
    args = parser.parse_args()
    
    print("RPi Optimized Crowd Detection")
    print("=" * 50)
    
    # Initialize detector
    detector = RPiCrowdDetector(
        weights=args.weights,
        img_size=args.img_size,
        conf_thres=args.conf_thres
    )
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Process
    if os.path.isfile(args.source):
        # Single image
        print(f"\nSingle image mode: {args.source}")
        output_path = os.path.join(args.output, f"result_{Path(args.source).name}")
        detector.detect_single_image(args.source, output_path, visualize=not args.no_vis)
        
    elif os.path.isdir(args.source):
        # Batch processing
        print(f"\nBatch processing mode: {args.source}")
        detector.batch_process(args.source, args.output, args.max_images)
        
    else:
        print(f"Path không hợp lệ: {args.source}")


# if __name__ == '__main__':
#     main()
