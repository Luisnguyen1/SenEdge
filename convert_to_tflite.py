import tensorflow as tf
import argparse

def convert_h5_to_tflite(h5_path, tflite_path):
    """Convert H5 model to TFLite format"""
    try:
        # Load the H5 model
        print(f"Loading H5 model from {h5_path}...")
        model = tf.keras.models.load_model(h5_path, compile=False)
        
        # Convert to TFLite
        print("Converting to TFLite format...")
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # Configure optimization
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Optional: Enable GPU acceleration
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,
            tf.lite.OpsSet.SELECT_TF_OPS
        ]
        
        # Convert model
        tflite_model = converter.convert()
        
        # Save the TFLite model
        print(f"Saving TFLite model to {tflite_path}...")
        with open(tflite_path, 'wb') as f:
            f.write(tflite_model)
            
        print("Conversion completed successfully!")
        
        # Print model size information
        h5_size = os.path.getsize(h5_path) / (1024 * 1024)
        tflite_size = os.path.getsize(tflite_path) / (1024 * 1024)
        print(f"\nModel size comparison:")
        print(f"H5 model: {h5_size:.2f} MB")
        print(f"TFLite model: {tflite_size:.2f} MB")
        print(f"Size reduction: {((h5_size - tflite_size) / h5_size * 100):.2f}%")
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        raise

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert H5 model to TFLite format')
    parser.add_argument('--input', '-i', required=True, help='Path to input H5 model')
    parser.add_argument('--output', '-o', required=True, help='Path for output TFLite model')
    args = parser.parse_args()
    
    # Convert model
    convert_h5_to_tflite(args.input, args.output)

if __name__ == "__main__":
    main()
