# This script is a Keras-based implementation for training a crowd detection model
import numpy as np
import tensorflow as tf
from tensorflow import keras
from Accuracy import Accuracy_Regression
import os

# Import Keras components
Sequential = keras.models.Sequential
Dense = keras.layers.Dense
Input = keras.layers.Input
InceptionResNetV2 = keras.applications.InceptionResNetV2
Adam = keras.optimizers.Adam
EarlyStopping = keras.callbacks.EarlyStopping
ReduceLROnPlateau = keras.callbacks.ReduceLROnPlateau

# Constants
AUTOTUNE = tf.data.experimental.AUTOTUNE
EPOCHS = 500
BATCH_SIZE = 8  # Reduced batch size
PATIENCE = 10
LEARNING_RATE = 1e-3
IMAGE_SIZE = 299

# File paths
IMAGES_NPY_PATH = 'Crowd_Density_Detection/images.npy'

# Configure GPU memory growth
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("GPU memory growth enabled")
    except RuntimeError as e:
        print(f"GPU configuration error: {e}")

def load_in_chunks(file_path, chunk_size=100):
    """Load and process data in chunks to save memory"""
    try:
        with np.load(file_path, mmap_mode='r') as X:
            total_samples = len(X)
            for start_idx in range(0, total_samples, chunk_size):
                end_idx = min(start_idx + chunk_size, total_samples)
                chunk = X[start_idx:end_idx].astype(np.float32)
                # Preprocess chunk
                chunk = tf.keras.applications.inception_resnet_v2.preprocess_input(chunk)
                yield chunk, end_idx == total_samples
    except Exception as e:
        print(f"Error in chunk loading: {e}")
        raise

def load_and_prepare_data():
    """Load and prepare data for training using chunked loading"""
    try:
        # Check if file exists
        if not os.path.exists(IMAGES_NPY_PATH):
            raise FileNotFoundError(f"Images file not found: {IMAGES_NPY_PATH}")

        # Get file size
        file_size = os.path.getsize(IMAGES_NPY_PATH) / (1024 * 1024 * 1024)  # in GB
        print(f"Dataset size: {file_size:.2f} GB")

        # Get total number of samples
        with np.load(IMAGES_NPY_PATH, mmap_mode='r') as X:
            total_samples = len(X)
            print(f"Total number of samples: {total_samples}")
            data_shape = X.shape[1:]
            print(f"Input shape: {data_shape}")

        # Initialize empty arrays for processed data
        X_processed = []
        chunk_size = 100  # Adjust this based on your available memory
        
        # Process data in chunks
        print("\nProcessing data in chunks:")
        for chunk, is_last in load_in_chunks(IMAGES_NPY_PATH, chunk_size):
            X_processed.append(chunk)
            print(f"Processed chunk of size {len(chunk)}", end='\r')

        # Combine processed chunks
        X_processed = np.concatenate(X_processed, axis=0)
        print(f"\nTotal processed samples: {len(X_processed)}")

        # Create dummy labels (replace with real labels)
        y = np.zeros(len(X_processed))
        
        # Split data
        train_size = int(0.85 * len(X_processed))
        X_train = X_processed[:train_size]
        X_valid = X_processed[train_size:]
        y_train = y[:train_size]
        y_valid = y[train_size:]
        
        print(f"Training set size: {len(X_train)}")
        print(f"Validation set size: {len(X_valid)}")
        
        return (X_train, y_train), (X_valid, y_valid)
    
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

def create_model():
    """Create and compile the model with memory optimization"""
    try:
        # Check available memory
        try:
            gpu = tf.config.list_physical_devices('GPU')[0]
            gpu_memory = tf.config.experimental.get_memory_info('GPU:0')
            print(f"GPU memory available: {gpu_memory['free'] / 1024**3:.2f} GB")
        except:
            print("No GPU available, using CPU")

        # Load pre-trained InceptionResNetV2
        base_model = InceptionResNetV2(
            include_top=False,
            weights='imagenet',
            input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
            pooling='avg'
        )
        base_model.trainable = False
        
        # Create model with mixed precision
        tf.keras.mixed_precision.set_global_policy('mixed_float16')
        
        model = Sequential([
            Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3)),
            base_model,
            Dense(512, activation='relu'),
            Dense(1, activation='linear')
        ])
        
        # Create accuracy metric
        accuracy_metric = Accuracy_Regression()
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=LEARNING_RATE),
            loss='mse',
            metrics=['mae', accuracy_metric.calculate]
        )
        
        return model, accuracy_metric
    
    except Exception as e:
        print(f"Error creating model: {e}")
        raise

def train_model(model, accuracy_metric, train_data, valid_data):
    """Train the model with memory-efficient data handling"""
    try:
        X_train, y_train = train_data
        X_valid, y_valid = valid_data
        
        # Convert to TF dataset for memory efficiency
        train_dataset = tf.data.Dataset.from_tensor_slices((X_train, y_train))\
            .batch(BATCH_SIZE)\
            .prefetch(AUTOTUNE)
        
        valid_dataset = tf.data.Dataset.from_tensor_slices((X_valid, y_valid))\
            .batch(BATCH_SIZE)\
            .prefetch(AUTOTUNE)
        
        # Initialize accuracy metric
        accuracy_metric.init(y_train)
        
        # Callbacks with ModelCheckpoint
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=PATIENCE,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.75,
                patience=1,
                cooldown=1,
                min_lr=1e-8,
                verbose=1
            )
        ]
        
        # Train with datasets
        history = model.fit(
            train_dataset,
            validation_data=valid_dataset,
            epochs=EPOCHS,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    except Exception as e:
        print(f"Error training model: {e}")
        raise

def save_model(model, path):
    """Save the model in H5 format"""
    try:
        model.save(path)
        print(f"Model saved successfully to {path}")
    except Exception as e:
        print(f"Error saving model: {e}")
        raise

def main():
    try:
        # Enable memory logging
        tf.debugging.set_log_device_placement(True)
        
        # Load and prepare data
        print("Loading and preparing data...")
        train_data, valid_data = load_and_prepare_data()
        
        # Create model
        print("Creating model...")
        model, accuracy_metric = create_model()
        model.summary()
        
        # Train model with error handling
        print("Training model...")
        try:
            history = train_model(model, accuracy_metric, train_data, valid_data)
        except tf.errors.ResourceExhaustedError:
            print("Out of memory error. Try reducing batch size or image size.")
            return
        except Exception as e:
            print(f"Training error: {e}")
            return
        
        # Evaluate model
        print("Evaluating model...")
        X_valid, y_valid = valid_data
        try:
            loss, mae, accuracy = model.evaluate(X_valid, y_valid, batch_size=BATCH_SIZE, verbose=1)
            print(f"\nValidation MAE: {mae:.4f}")
            print(f"Validation Accuracy: {accuracy*100:.2f}%")
        except Exception as e:
            print(f"Evaluation error: {e}")
            return
        
        # Save model
        try:
            save_model(model, 'crowd_detection_model.h5')
        except Exception as e:
            print(f"Error saving model: {e}")
            return
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
