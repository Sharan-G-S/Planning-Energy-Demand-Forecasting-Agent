"""
Data Preprocessing and Feature Engineering
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import config

class DataPreprocessor:
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        
    def create_lag_features(self, df, column='energy_demand', lags=None):
        """Create lag features for time series"""
        if lags is None:
            lags = config.LAG_FEATURES
        
        df_copy = df.copy()
        for lag in lags:
            df_copy[f'{column}_lag_{lag}'] = df_copy[column].shift(lag)
        
        return df_copy
    
    def create_rolling_features(self, df, column='energy_demand', windows=[24, 168]):
        """Create rolling mean and std features"""
        df_copy = df.copy()
        for window in windows:
            df_copy[f'{column}_rolling_mean_{window}'] = df_copy[column].rolling(window=window).mean()
            df_copy[f'{column}_rolling_std_{window}'] = df_copy[column].rolling(window=window).std()
        
        return df_copy
    
    def create_time_features(self, df):
        """Extract time-based features from timestamp"""
        df_copy = df.copy()
        
        if 'timestamp' in df_copy.columns:
            df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
            df_copy['hour'] = df_copy['timestamp'].dt.hour
            df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek
            df_copy['month'] = df_copy['timestamp'].dt.month
            df_copy['day_of_year'] = df_copy['timestamp'].dt.dayofyear
            df_copy['is_weekend'] = (df_copy['day_of_week'] >= 5).astype(int)
            
            # Cyclical encoding for hour and month
            df_copy['hour_sin'] = np.sin(2 * np.pi * df_copy['hour'] / 24)
            df_copy['hour_cos'] = np.cos(2 * np.pi * df_copy['hour'] / 24)
            df_copy['month_sin'] = np.sin(2 * np.pi * df_copy['month'] / 12)
            df_copy['month_cos'] = np.cos(2 * np.pi * df_copy['month'] / 12)
        
        return df_copy
    
    def handle_missing_values(self, df):
        """Handle missing values using forward fill and interpolation"""
        df_copy = df.copy()
        
        # Forward fill for small gaps
        df_copy = df_copy.fillna(method='ffill', limit=3)
        
        # Interpolate for larger gaps
        df_copy = df_copy.interpolate(method='linear')
        
        # Drop remaining NaN values
        df_copy = df_copy.dropna()
        
        return df_copy
    
    def scale_features(self, data, fit=True):
        """Scale features to [0, 1] range"""
        if fit:
            scaled = self.scaler.fit_transform(data.reshape(-1, 1))
        else:
            scaled = self.scaler.transform(data.reshape(-1, 1))
        return scaled.flatten()
    
    def inverse_scale(self, data):
        """Inverse transform scaled data"""
        return self.scaler.inverse_transform(data.reshape(-1, 1)).flatten()
    
    def prepare_lstm_data(self, df, sequence_length=24, target_column='energy_demand'):
        """Prepare data for LSTM model"""
        # Create features
        df = self.create_time_features(df)
        df = self.create_lag_features(df, target_column)
        df = self.create_rolling_features(df, target_column)
        df = self.handle_missing_values(df)
        
        # Select feature columns
        feature_columns = [
            'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
            'day_of_week', 'is_weekend', 'temperature'
        ]
        
        # Add lag features if they exist
        lag_cols = [col for col in df.columns if 'lag' in col or 'rolling' in col]
        feature_columns.extend(lag_cols)
        
        # Ensure all feature columns exist
        feature_columns = [col for col in feature_columns if col in df.columns]
        
        # Scale target
        target_data = df[target_column].values
        scaled_target = self.scale_features(target_data, fit=True)
        
        # Scale features
        if len(feature_columns) > 0:
            feature_data = df[feature_columns].values
            scaled_features = self.feature_scaler.fit_transform(feature_data)
        else:
            scaled_features = np.zeros((len(df), 1))
        
        # Create sequences
        X, y = [], []
        for i in range(sequence_length, len(scaled_target)):
            # Combine target history with features
            target_seq = scaled_target[i-sequence_length:i].reshape(-1, 1)
            feature_seq = scaled_features[i-sequence_length:i]
            
            combined_seq = np.concatenate([target_seq, feature_seq], axis=1)
            X.append(combined_seq)
            y.append(scaled_target[i])
        
        return np.array(X), np.array(y), feature_columns
    
    def prepare_prophet_data(self, df, target_column='energy_demand'):
        """Prepare data for Prophet model"""
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df['timestamp']),
            'y': df[target_column]
        })
        return prophet_df

if __name__ == "__main__":
    # Test preprocessing
    from data_generator import EnergyDataGenerator
    
    generator = EnergyDataGenerator(days=30)
    df = generator.generate_data()
    
    preprocessor = DataPreprocessor()
    X, y, features = preprocessor.prepare_lstm_data(df)
    
    print(f"LSTM data shape: X={X.shape}, y={y.shape}")
    print(f"Features used: {features}")
