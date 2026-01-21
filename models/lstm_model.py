"""
LSTM Neural Network for Energy Demand Forecasting
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import config
import os

class LSTMForecaster:
    def __init__(self, sequence_length=24, n_features=8):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.history = None
        
    def build_model(self):
        """Build LSTM model architecture"""
        model = keras.Sequential([
            layers.LSTM(
                config.LSTM_CONFIG['hidden_units'],
                activation='tanh',
                return_sequences=True,
                input_shape=(self.sequence_length, self.n_features)
            ),
            layers.Dropout(config.LSTM_CONFIG['dropout_rate']),
            
            layers.LSTM(
                config.LSTM_CONFIG['hidden_units'] // 2,
                activation='tanh',
                return_sequences=False
            ),
            layers.Dropout(config.LSTM_CONFIG['dropout_rate']),
            
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu'),
            layers.Dense(1)
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train the LSTM model"""
        if self.model is None:
            self.build_model()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
        ]
        
        # Train
        validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None
        
        self.history = self.model.fit(
            X_train, y_train,
            epochs=config.LSTM_CONFIG['epochs'],
            batch_size=config.LSTM_CONFIG['batch_size'],
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=0
        )
        
        return self.history
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        predictions = self.model.predict(X, verbose=0)
        return predictions.flatten()
    
    def predict_sequence(self, initial_sequence, n_steps, features=None):
        """Predict multiple steps ahead"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        predictions = []
        current_sequence = initial_sequence.copy()
        
        for i in range(n_steps):
            # Predict next step
            pred = self.model.predict(current_sequence.reshape(1, self.sequence_length, self.n_features), verbose=0)
            predictions.append(pred[0, 0])
            
            # Update sequence
            new_row = np.zeros((1, self.n_features))
            new_row[0, 0] = pred[0, 0]  # Predicted value
            
            # Add features if provided
            if features is not None and i < len(features):
                new_row[0, 1:] = features[i]
            else:
                # Use last known features
                new_row[0, 1:] = current_sequence[-1, 1:]
            
            # Shift sequence
            current_sequence = np.vstack([current_sequence[1:], new_row])
        
        return np.array(predictions)
    
    def save_model(self, filepath='saved_models/lstm_model.h5'):
        """Save trained model"""
        if self.model is None:
            raise ValueError("No model to save!")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath='saved_models/lstm_model.h5'):
        """Load trained model"""
        if os.path.exists(filepath):
            self.model = keras.models.load_model(filepath)
            print(f"Model loaded from {filepath}")
            return True
        return False
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)
        
        predictions = self.predict(X_test)
        
        # Calculate additional metrics
        mse = np.mean((predictions - y_test) ** 2)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        
        return {
            'loss': loss,
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape
        }

if __name__ == "__main__":
    # Test LSTM model
    print("Testing LSTM Forecaster...")
    
    # Create dummy data
    X_train = np.random.rand(1000, 24, 8)
    y_train = np.random.rand(1000)
    X_test = np.random.rand(200, 24, 8)
    y_test = np.random.rand(200)
    
    # Build and train
    forecaster = LSTMForecaster(sequence_length=24, n_features=8)
    forecaster.build_model()
    print("Model architecture:")
    forecaster.model.summary()
    
    print("\nTraining model...")
    history = forecaster.train(X_train, y_train, X_test, y_test)
    
    # Evaluate
    metrics = forecaster.evaluate(X_test, y_test)
    print("\nModel Performance:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
