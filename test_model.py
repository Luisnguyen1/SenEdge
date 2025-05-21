import numpy as np
import tensorflow as tf
from tensorflow import keras
import PIL
from PIL import Image
import os

def is_image_file(filename):
    """Check if file is an image"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    return any(filename.endswith(ext) for ext in valid_extensions)

def convert_image_to_array(image_path):
    """Convert JPG/PNG image to numpy array"""
    try:
        # Open image
        img = Image.open(image_path)
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Convert to numpy array
        img_array = np.array(img)
        print(f"Converted image shape: {img_array.shape}")
        return img_array
    except Exception as e:
        print(f"Error converting image: {e}")
        raise

def load_model(model_path):
    """Load the trained model"""
    try:
        model = keras.models.load_model(model_path)
        print("Model loaded successfully!")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

def prepare_image(image, target_size=(299, 299)):
    """Prepare single image for prediction"""
    # Resize image
    image = tf.image.resize_with_pad(image, target_size[0], target_size[1])
    # Preprocess
    image = keras.applications.inception_resnet_v2.preprocess_input(image)
    # Add batch dimension
    image = np.expand_dims(image, axis=0)
    return image

def predict_crowd(model, image_path):
    """Make prediction on single image"""
    try:
        # Check file type and load image
        if is_image_file(image_path):
            print("Loading image file...")
            image = convert_image_to_array(image_path)
        elif image_path.endswith('.npy'):
            print("Loading numpy file...")
            image = np.load(image_path)
        else:
            raise ValueError("Unsupported file format. Please use JPG, PNG or NPY files.")

        # Prepare image
        processed_image = prepare_image(image)
        print(f"Processed image shape: {processed_image.shape}")
        
        # Make prediction
        prediction = model.predict(processed_image, verbose=0)
        return prediction[0][0]
    except Exception as e:
        print(f"Error making prediction: {e}")
        raise

def main():
    try:
        # Path to saved model
        MODEL_PATH = 'crowd_detection_model.h5'
        
        # Get image path from user input
        image_path = input("Enter the path to your image (JPG, PNG, or NPY file): ").strip()
        
        # Load model
        print("Loading model...")
        model = load_model(MODEL_PATH)
        
        # Validate file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Make prediction
        print("\nMaking prediction...")
        crowd_count = predict_crowd(model, image_path)
        print(f"\nPredicted crowd count: {crowd_count:.2f}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
