# This script is a Keras-based implementation for training a crowd detection model using the InceptionResNetV2 architecture. It includes data loading, preprocessing, model creation, training, evaluation, and saving the model.

import numpy as np
import tensorflow as tf
from tensorflow import keras
from Accuracy import Accuracy_Regression  # Add Accuracy import

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
BATCH_SIZE = 16
PATIENCE = 10
LEARNING_RATE = 1e-3
IMAGE_SIZE = 299

# File paths
IMAGES_NPY_PATH = '/home/trang/Downloads/images.npy'

def load_and_prepare_data():
    """Load and prepare data for training"""
    try:
        # Load images
        print("Loading images...")
        X = np.load(IMAGES_NPY_PATH)
        print(f"Loaded images shape: {X.shape}")
        
        # Preprocess images
        X = tf.keras.applications.inception_resnet_v2.preprocess_input(X)
        
        # Create dummy labels for testing (replace with real labels)
        y = np.zeros(X.shape[0])
        
        # Split data
        train_size = int(0.85 * len(X))
        X_train = X[:train_size]
        X_valid = X[train_size:]
        y_train = y[:train_size]
        y_valid = y[train_size:]
        
        print(f"Training set size: {len(X_train)}")
        print(f"Validation set size: {len(X_valid)}")
        
        return (X_train, y_train), (X_valid, y_valid)
    
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

def create_model():
    """Create and compile the model"""
    try:
        # Load pre-trained InceptionResNetV2
        base_model = InceptionResNetV2(
            include_top=False,
            weights='imagenet',
            input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
            pooling='avg'
        )
        base_model.trainable = False
        
        # Create model
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
    """Train the model"""
    try:
        X_train, y_train = train_data
        X_valid, y_valid = valid_data
        
        # Initialize accuracy metric
        accuracy_metric.init(y_train)
        
        # Callbacks
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
        
        # Train
        history = model.fit(
            X_train, y_train,
            validation_data=(X_valid, y_valid),
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
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
        # Load and prepare data
        print("Loading and preparing data...")
        train_data, valid_data = load_and_prepare_data()
        
        # Create model
        print("Creating model...")
        model, accuracy_metric = create_model()
        model.summary()
        
        # Train model
        print("Training model...")
        history = train_model(model, accuracy_metric, train_data, valid_data)
        
        # Evaluate model
        X_valid, y_valid = valid_data
        loss, mae, accuracy = model.evaluate(X_valid, y_valid, verbose=0)
        print(f"\nValidation MAE: {mae:.4f}")
        print(f"Validation Accuracy: {accuracy*100:.2f}%")
        
        # Save model
        save_model(model, 'crowd_detection_model.h5')
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
