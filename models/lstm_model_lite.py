"""
Simplified LSTM Model (using sklearn instead of TensorFlow for faster testing)
This is a lightweight version for demonstration. For production, use the full TensorFlow version.
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import config
import os
import pickle

class LSTMForecaster:
    def __init__(self, sequence_length=24, n_features=8):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.scaler = StandardScaler()
        self.history = None
        
    def build_model(self):
        """Build MLP model as LSTM alternative"""
        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            max_iter=100,
            early_stopping=True,
            validation_fraction=0.2,
            random_state=42,
            verbose=False
        )
        return self.model
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train the model"""
        if self.model is None:
            self.build_model()
        
        # Reshape for MLP (flatten sequences)
        X_train_flat = X_train.reshape(X_train.shape[0], -1)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train_flat)
        
        # Train
        self.model.fit(X_train_scaled, y_train)
        
        return self
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        X_flat = X.reshape(X.shape[0], -1)
        X_scaled = self.scaler.transform(X_flat)
        predictions = self.model.predict(X_scaled)
        return predictions
    
    def predict_sequence(self, initial_sequence, n_steps, features=None):
        """Predict multiple steps ahead"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        predictions = []
        current_sequence = initial_sequence.copy()
        
        for i in range(n_steps):
            # Predict next step
            X_flat = current_sequence.reshape(1, -1)
            X_scaled = self.scaler.transform(X_flat)
            pred = self.model.predict(X_scaled)
            predictions.append(pred[0])
            
            # Update sequence
            new_row = np.zeros((1, self.n_features))
            new_row[0, 0] = pred[0]
            
            if features is not None and i < len(features):
                new_row[0, 1:] = features[i]
            else:
                new_row[0, 1:] = current_sequence[-1, 1:]
            
            current_sequence = np.vstack([current_sequence[1:], new_row])
        
        return np.array(predictions)
    
    def save_model(self, filepath='saved_models/lstm_model.pkl'):
        """Save trained model"""
        if self.model is None:
            raise ValueError("No model to save!")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath='saved_models/lstm_model.pkl'):
        """Load trained model"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
            print(f"Model loaded from {filepath}")
            return True
        return False
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        predictions = self.predict(X_test)
        
        mse = np.mean((predictions - y_test) ** 2)
        mae = np.mean(np.abs(predictions - y_test))
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        
        return {
            'loss': mse,
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape
        }

if __name__ == "__main__":
    print("Testing LSTM Forecaster (sklearn version)...")
    
    X_train = np.random.rand(1000, 24, 8)
    y_train = np.random.rand(1000)
    X_test = np.random.rand(200, 24, 8)
    y_test = np.random.rand(200)
    
    forecaster = LSTMForecaster(sequence_length=24, n_features=8)
    forecaster.build_model()
    print("Model built successfully")
    
    print("\nTraining model...")
    forecaster.train(X_train, y_train, X_test, y_test)
    
    metrics = forecaster.evaluate(X_test, y_test)
    print("\nModel Performance:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
