"""
Configuration settings for Energy Demand Forecasting Agent
"""

import os

# Application Settings
DEBUG = True
HOST = '0.0.0.0'
PORT = 5001

# Data Generation Settings
HISTORICAL_DAYS = 365  # Generate 1 year of historical data
FORECAST_HOURS_DEFAULT = 24
FORECAST_DAYS_MAX = 30

# Model Settings
LSTM_CONFIG = {
    'sequence_length': 24,  # Use 24 hours of history
    'hidden_units': 64,
    'dropout_rate': 0.2,
    'epochs': 50,
    'batch_size': 32,
    'validation_split': 0.2
}

PROPHET_CONFIG = {
    'changepoint_prior_scale': 0.05,
    'seasonality_prior_scale': 10.0,
    'daily_seasonality': True,
    'weekly_seasonality': True,
    'yearly_seasonality': True
}

ENSEMBLE_WEIGHTS = {
    'lstm': 0.6,
    'prophet': 0.4
}

# Grid Optimization Settings
PEAK_THRESHOLD = 0.85  # 85% of max capacity
OPTIMAL_LOAD_RANGE = (0.4, 0.7)  # 40-70% of max capacity
MAX_GRID_CAPACITY = 10000  # MW

# Anomaly Detection Settings
ANOMALY_THRESHOLD = 3.0  # Z-score threshold
ANOMALY_WINDOW = 24  # Hours to check for anomalies

# Feature Engineering
WEATHER_IMPACT = True
HOLIDAY_IMPACT = True
LAG_FEATURES = [1, 24, 168]  # 1h, 1d, 1w lags

# Data Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'saved_models')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
