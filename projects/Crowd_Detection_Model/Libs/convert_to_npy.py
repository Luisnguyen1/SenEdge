import os
import numpy as np
from PIL import Image
from tqdm import tqdm
import argparse

def is_image_file(filename):
    """Check if file is a valid image"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    return any(filename.endswith(ext) for ext in valid_extensions)

def convert_image_to_array(image_path, target_size=(640, 480)):
    """Convert single image to numpy array with resizing"""
    try:
        # Open and convert to RGB
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize image
        if img.size != target_size:
            print(f"Resizing from {img.size} to {target_size}")
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
        # Convert to numpy array
        array = np.array(img)
        return array
    except Exception as e:
        print(f"Error converting {image_path}: {e}")
        return None

def get_npy_shape(npy_path):
    """
    Read sample shape from .npy file without loading entire file
    Returns: tuple (sample_shape, total_samples)
    """
    try:
        # Open .npy file in mmap mode to read only header
        with np.lib.format.open_memmap(npy_path, mode='r') as mmap_array:
            total_samples = mmap_array.shape[0]  # Number of samples
            sample_shape = mmap_array.shape[1:]  # Shape of each sample
            del mmap_array  # Close memmap immediately to free resources
            
        return sample_shape, total_samples
    except Exception as e:
        raise ValueError(f"Error reading .npy file: {str(e)}")

def process_image_directory(input_dir, output_path, target_size=(640, 480)):
    """Convert all images in directory to single .npy file"""
    try:
        # Get list of image files
        image_files = [f for f in os.listdir(input_dir) if is_image_file(f)]
        if not image_files:
            raise ValueError(f"No valid image files found in {input_dir}")
        
        print(f"Found {len(image_files)} images")
        
        # Convert images to arrays
        image_arrays = []
        for img_file in tqdm(image_files, desc="Converting images"):
            img_path = os.path.join(input_dir, img_file)
            img_array = convert_image_to_array(img_path, target_size)
            if img_array is not None:
                image_arrays.append(img_array)
        
        if not image_arrays:
            raise ValueError("No images were successfully converted")
        
        # Stack arrays and save
        images = np.stack(image_arrays)
        print(f"\nFinal array shape: {images.shape}")
        
        # Save to .npy file
        np.save(output_path, images)
        print(f"Successfully saved to {output_path}")
        
        return images.shape[0]  # Return number of processed images
        
    except Exception as e:
        print(f"Error processing directory: {e}")
        raise

def append_to_existing_npy(existing_npy_path, new_images_dir, target_size=(640, 480)):
    """Append new images to existing .npy file"""
    try:
        # Check if file exists and is readable
        if not os.path.exists(existing_npy_path):
            raise FileNotFoundError(f"File not found: {existing_npy_path}")
            
        file_size = os.path.getsize(existing_npy_path) / (1024 * 1024)  # Convert to MB
        print(f"\nCurrent .npy file size: {file_size:.2f} MB")
        
        # Read file information
        print("Reading .npy file information...")
        sample_shape, total_samples = get_npy_shape(existing_npy_path)
        print(f"Current number of samples: {total_samples}")
        print(f"Sample shape: {sample_shape}")
        
        if len(sample_shape) != 3:  # height, width, channels
            raise ValueError("Invalid .npy file format. Required shape: (n, height, width, channels)")
            
        print(f"Target image size: {target_size[0]}x{target_size[1]} pixels")
        
        # Process new images
        print("\nProcessing new images...")
        image_files = [f for f in os.listdir(new_images_dir) if is_image_file(f)]
        new_arrays = []
        
        for img_file in tqdm(image_files, desc="Converting images"):
            img_path = os.path.join(new_images_dir, img_file)
            img_array = convert_image_to_array(img_path, target_size)
            if img_array is not None:
                new_arrays.append(img_array)
        
        if not new_arrays:
            raise ValueError("No new images were successfully converted")
        
        # Stack new arrays and append using memmap
        new_images = np.stack(new_arrays)
        with np.lib.format.open_memmap(existing_npy_path, mode='r+') as mmap_array:
            new_size = total_samples + len(new_arrays)
            new_shape = (new_size,) + sample_shape
            mmap_array.resize(new_shape, refcheck=False)
            mmap_array[total_samples:] = new_images
            
        print(f"\nNew array shape: {new_shape}")
        print(f"Successfully updated {existing_npy_path}")
        
        return len(new_arrays)  # Return number of added images
        
    except Exception as e:
        print(f"Error appending images: {str(e)}")
        raise

def get_user_choice():
    """Display menu and get user choice"""
    while True:
        print("\n=== IMAGE CONVERSION MENU ===")
        print("1. Convert images to new .npy file")
        print("2. Add images to existing .npy file")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ")
            if choice in ['1', '2', '3']:
                return choice
            else:
                print("Invalid choice. Please select 1-3.")
        except Exception:
            print("An error occurred. Please try again.")

def main():
    try:
        while True:
            choice = get_user_choice()
            
            if choice == '3':
                print("\nGoodbye!")
                break
                
            # Get input directory
            input_dir = input("\nEnter images directory path: ").strip()
            if not os.path.isdir(input_dir):
                print(f"Error: Directory {input_dir} does not exist!")
                continue
            
            if choice == '1':
                # Convert to new .npy file
                output_path = input("Enter output .npy file path (default: converted_images.npy): ").strip()
                if not output_path:
                    output_path = 'converted_images.npy'
                
                num_processed = process_image_directory(input_dir, output_path)
                print(f"\nSuccessfully processed {num_processed} images")
                
            elif choice == '2':
                # Add to existing .npy file
                existing_npy = input("Enter existing .npy file path: ").strip()
                if not os.path.exists(existing_npy):
                    print(f"Error: File {existing_npy} does not exist!")
                    continue
                
                print("Using default size: 640x480 pixels")
                try:
                    num_added = append_to_existing_npy(existing_npy, input_dir)
                    if num_added:
                        print(f"\nSuccessfully added {num_added} images")
                except Exception as e:
                    print(f"\nError adding images: {str(e)}")
                    continue

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nPress Enter to exit...")
        input()

if __name__ == "__main__":
    main()
