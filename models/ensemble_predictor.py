"""
Ensemble Predictor combining LSTM and Prophet models
"""

import numpy as np
import pandas as pd
import config
from models.lstm_model import LSTMForecaster
from models.prophet_model import ProphetForecaster
from utils.preprocessor import DataPreprocessor

class EnsemblePredictor:
    def __init__(self):
        self.lstm_model = LSTMForecaster()
        self.prophet_model = ProphetForecaster()
        self.preprocessor = DataPreprocessor()
        self.weights = config.ENSEMBLE_WEIGHTS
        self.trained = False
        
    def train(self, df, target_column='energy_demand'):
        """Train both models"""
        print("Training ensemble models...")
        
        # Train Prophet
        print("Training Prophet model...")
        prophet_df = self.preprocessor.prepare_prophet_data(df, target_column)
        self.prophet_model.train(prophet_df)
        
        # Train LSTM
        print("Training LSTM model...")
        X, y, features = self.preprocessor.prepare_lstm_data(df, target_column=target_column)
        
        # Split train/val
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.lstm_model.n_features = X.shape[2]
        self.lstm_model.train(X_train, y_train, X_val, y_val)
        
        self.trained = True
        print("Ensemble training complete!")
        
        return True
    
    def predict_lstm(self, df, hours_ahead=24, target_column='energy_demand'):
        """Get LSTM predictions"""
        # Prepare data
        X, _, _ = self.preprocessor.prepare_lstm_data(df, target_column=target_column)
        
        if len(X) == 0:
            return None
        
        # Use last sequence for prediction
        last_sequence = X[-1]
        
        # Predict future
        predictions = self.lstm_model.predict_sequence(last_sequence, hours_ahead)
        
        # Inverse transform
        predictions_scaled = self.preprocessor.inverse_scale(predictions)
        
        return predictions_scaled
    
    def predict_prophet(self, hours_ahead=24):
        """Get Prophet predictions"""
        forecast = self.prophet_model.predict_future(periods=hours_ahead, freq='H')
        return forecast['yhat'].values
    
    def predict(self, df, hours_ahead=24, target_column='energy_demand'):
        """
        Generate ensemble predictions
        Returns predictions with uncertainty bounds
        """
        if not self.trained:
            raise ValueError("Models not trained yet!")
        
        # Get predictions from both models
        try:
            lstm_pred = self.predict_lstm(df, hours_ahead, target_column)
        except Exception as e:
            print(f"LSTM prediction failed: {e}")
            lstm_pred = None
        
        try:
            prophet_pred = self.predict_prophet(hours_ahead)
        except Exception as e:
            print(f"Prophet prediction failed: {e}")
            prophet_pred = None
        
        # Combine predictions
        if lstm_pred is not None and prophet_pred is not None:
            # Weighted average
            ensemble_pred = (self.weights['lstm'] * lstm_pred + 
                           self.weights['prophet'] * prophet_pred)
            
            # Calculate uncertainty based on disagreement
            disagreement = np.abs(lstm_pred - prophet_pred)
            uncertainty = disagreement * 0.5
            
        elif lstm_pred is not None:
            ensemble_pred = lstm_pred
            uncertainty = lstm_pred * 0.1  # 10% uncertainty
            
        elif prophet_pred is not None:
            ensemble_pred = prophet_pred
            uncertainty = prophet_pred * 0.1
            
        else:
            raise ValueError("Both models failed to predict!")
        
        # Generate timestamps
        last_timestamp = pd.to_datetime(df['timestamp'].iloc[-1])
        future_timestamps = [last_timestamp + pd.Timedelta(hours=i+1) for i in range(hours_ahead)]
        
        # Create result dataframe
        results = pd.DataFrame({
            'timestamp': future_timestamps,
            'predicted_demand': ensemble_pred,
            'lower_bound': ensemble_pred - uncertainty,
            'upper_bound': ensemble_pred + uncertainty,
            'lstm_prediction': lstm_pred if lstm_pred is not None else ensemble_pred,
            'prophet_prediction': prophet_pred if prophet_pred is not None else ensemble_pred
        })
        
        return results
    
    def predict_with_confidence(self, df, hours_ahead=24, target_column='energy_demand'):
        """Generate predictions with confidence scores"""
        predictions = self.predict(df, hours_ahead, target_column)
        
        # Calculate confidence based on uncertainty
        predictions['confidence'] = 100 * (1 - (predictions['upper_bound'] - predictions['lower_bound']) / 
                                          (2 * predictions['predicted_demand']))
        predictions['confidence'] = predictions['confidence'].clip(0, 100)
        
        return predictions
    
    def evaluate(self, test_df, target_column='energy_demand'):
        """Evaluate ensemble performance"""
        if not self.trained:
            raise ValueError("Models not trained yet!")
        
        # Get predictions for test period
        predictions = self.predict(test_df[:-24], hours_ahead=24, target_column=target_column)
        
        # Compare with actual
        actual = test_df[target_column].tail(24).values
        predicted = predictions['predicted_demand'].values
        
        # Calculate metrics
        mae = np.mean(np.abs(actual - predicted))
        mse = np.mean((actual - predicted) ** 2)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # Check interval coverage
        in_interval = ((actual >= predictions['lower_bound'].values) & 
                      (actual <= predictions['upper_bound'].values))
        coverage = np.mean(in_interval) * 100
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape,
            'interval_coverage': coverage
        }
    
    def save_models(self):
        """Save both models"""
        self.lstm_model.save_model('saved_models/lstm_model.h5')
        # Prophet model is saved automatically during training
        print("Models saved successfully!")
    
    def load_models(self):
        """Load both models"""
        success = self.lstm_model.load_model('saved_models/lstm_model.h5')
        if success:
            self.trained = True
            print("Models loaded successfully!")
        return success

if __name__ == "__main__":
    # Test ensemble predictor
    from utils.data_generator import EnergyDataGenerator
    
    print("Testing Ensemble Predictor...")
    
    # Generate data
    generator = EnergyDataGenerator(days=60)
    df = generator.generate_data()
    
    # Train ensemble
    ensemble = EnsemblePredictor()
    ensemble.train(df)
    
    # Predict
    predictions = ensemble.predict_with_confidence(df, hours_ahead=24)
    print("\nPredictions:")
    print(predictions.head())
    
    # Evaluate
    metrics = ensemble.evaluate(df)
    print("\nEnsemble Performance:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
