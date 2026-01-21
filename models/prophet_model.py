"""
Facebook Prophet Model for Energy Demand Forecasting
"""

import pandas as pd
import numpy as np
from prophet import Prophet
import config
import warnings
warnings.filterwarnings('ignore')

class ProphetForecaster:
    def __init__(self):
        self.model = None
        self.fitted = False
        
    def build_model(self):
        """Build Prophet model with custom configuration"""
        model = Prophet(
            changepoint_prior_scale=config.PROPHET_CONFIG['changepoint_prior_scale'],
            seasonality_prior_scale=config.PROPHET_CONFIG['seasonality_prior_scale'],
            daily_seasonality=config.PROPHET_CONFIG['daily_seasonality'],
            weekly_seasonality=config.PROPHET_CONFIG['weekly_seasonality'],
            yearly_seasonality=config.PROPHET_CONFIG['yearly_seasonality'],
            interval_width=0.95
        )
        
        # Add custom seasonalities
        model.add_seasonality(name='hourly', period=1, fourier_order=8)
        
        self.model = model
        return model
    
    def train(self, df):
        """
        Train Prophet model
        df should have columns: 'ds' (datetime) and 'y' (target)
        """
        if self.model is None:
            self.build_model()
        
        # Ensure proper format
        train_df = df[['ds', 'y']].copy()
        train_df['ds'] = pd.to_datetime(train_df['ds'])
        
        # Fit model
        self.model.fit(train_df)
        self.fitted = True
        
        return self.model
    
    def predict(self, periods=24, freq='H'):
        """
        Make future predictions
        periods: number of time periods to forecast
        freq: frequency ('H' for hourly, 'D' for daily)
        """
        if not self.fitted:
            raise ValueError("Model not trained yet!")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        
        # Predict
        forecast = self.model.predict(future)
        
        return forecast
    
    def predict_future(self, periods=24, freq='H'):
        """Get only future predictions (not historical)"""
        forecast = self.predict(periods, freq)
        
        # Return only future predictions
        future_forecast = forecast.tail(periods)
        
        return future_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    def get_components(self):
        """Get forecast components (trend, seasonality)"""
        if not self.fitted:
            raise ValueError("Model not trained yet!")
        
        # Make prediction for analysis
        future = self.model.make_future_dataframe(periods=24, freq='H')
        forecast = self.model.predict(future)
        
        components = {
            'trend': forecast[['ds', 'trend']].to_dict('records'),
            'weekly': forecast[['ds', 'weekly']].to_dict('records') if 'weekly' in forecast.columns else None,
            'daily': forecast[['ds', 'daily']].to_dict('records') if 'daily' in forecast.columns else None,
            'yearly': forecast[['ds', 'yearly']].to_dict('records') if 'yearly' in forecast.columns else None
        }
        
        return components
    
    def evaluate(self, test_df):
        """
        Evaluate model on test data
        test_df should have columns: 'ds' and 'y'
        """
        if not self.fitted:
            raise ValueError("Model not trained yet!")
        
        # Predict for test period
        forecast = self.model.predict(test_df[['ds']])
        
        # Calculate metrics
        y_true = test_df['y'].values
        y_pred = forecast['yhat'].values
        
        mae = np.mean(np.abs(y_true - y_pred))
        mse = np.mean((y_true - y_pred) ** 2)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # Coverage of prediction intervals
        in_interval = ((y_true >= forecast['yhat_lower'].values) & 
                      (y_true <= forecast['yhat_upper'].values))
        coverage = np.mean(in_interval) * 100
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape,
            'interval_coverage': coverage
        }
    
    def get_forecast_with_uncertainty(self, periods=24, freq='H'):
        """Get forecast with uncertainty intervals"""
        forecast = self.predict_future(periods, freq)
        
        results = []
        for _, row in forecast.iterrows():
            results.append({
                'timestamp': row['ds'].isoformat(),
                'prediction': float(row['yhat']),
                'lower_bound': float(row['yhat_lower']),
                'upper_bound': float(row['yhat_upper']),
                'uncertainty': float(row['yhat_upper'] - row['yhat_lower'])
            })
        
        return results

if __name__ == "__main__":
    # Test Prophet model
    print("Testing Prophet Forecaster...")
    
    # Create dummy data
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='H')
    values = 5000 + 1000 * np.sin(np.arange(1000) * 2 * np.pi / 24) + np.random.normal(0, 100, 1000)
    
    train_df = pd.DataFrame({
        'ds': dates[:800],
        'y': values[:800]
    })
    
    test_df = pd.DataFrame({
        'ds': dates[800:],
        'y': values[800:]
    })
    
    # Build and train
    forecaster = ProphetForecaster()
    forecaster.build_model()
    forecaster.train(train_df)
    
    print("Model trained successfully!")
    
    # Predict
    forecast = forecaster.predict_future(periods=24)
    print(f"\nForecast shape: {forecast.shape}")
    print("\nSample predictions:")
    print(forecast.head())
    
    # Evaluate
    metrics = forecaster.evaluate(test_df)
    print("\nModel Performance:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
