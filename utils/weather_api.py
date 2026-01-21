"""
Real-time Weather API Integration
Fetches current weather data to enhance energy demand predictions
"""

import requests
import pandas as pd
from datetime import datetime
import os

class WeatherAPI:
    def __init__(self, api_key=None, location="New York"):
        """
        Initialize Weather API client
        For production, use OpenWeatherMap or similar service
        For demo, we'll simulate weather data
        """
        self.api_key = api_key or os.environ.get('WEATHER_API_KEY')
        self.location = location
        self.use_simulation = True  # Set to False when API key is available
        
    def get_current_weather(self):
        """Get current weather conditions"""
        if self.use_simulation:
            return self._simulate_weather()
        
        # Real API integration (requires API key)
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': self.location,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'conditions': data['weather'][0]['main'],
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Weather API error: {e}, using simulation")
            return self._simulate_weather()
    
    def _simulate_weather(self):
        """Simulate realistic weather data"""
        import numpy as np
        
        # Simulate temperature based on time of day
        hour = datetime.now().hour
        base_temp = 20 + 10 * np.sin((hour - 6) * np.pi / 12)
        
        return {
            'temperature': round(base_temp + np.random.normal(0, 2), 1),
            'humidity': round(60 + np.random.normal(0, 10), 1),
            'pressure': round(1013 + np.random.normal(0, 5), 1),
            'wind_speed': round(abs(np.random.normal(5, 2)), 1),
            'conditions': np.random.choice(['Clear', 'Clouds', 'Rain', 'Partly Cloudy']),
            'timestamp': datetime.now()
        }
    
    def get_forecast(self, hours=24):
        """Get weather forecast for next N hours"""
        if self.use_simulation:
            return self._simulate_forecast(hours)
        
        # Real API integration
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast"
            params = {
                'q': self.location,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': min(hours // 3, 40)  # API returns 3-hour intervals
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            forecast = []
            for item in data['list']:
                forecast.append({
                    'timestamp': datetime.fromtimestamp(item['dt']),
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'pressure': item['main']['pressure'],
                    'wind_speed': item['wind']['speed'],
                    'conditions': item['weather'][0]['main']
                })
            
            return pd.DataFrame(forecast)
        except Exception as e:
            print(f"Weather forecast error: {e}, using simulation")
            return self._simulate_forecast(hours)
    
    def _simulate_forecast(self, hours):
        """Simulate weather forecast"""
        import numpy as np
        from datetime import timedelta
        
        forecast = []
        base_time = datetime.now()
        
        for i in range(hours):
            hour = (base_time + timedelta(hours=i)).hour
            base_temp = 20 + 10 * np.sin((hour - 6) * np.pi / 12)
            
            forecast.append({
                'timestamp': base_time + timedelta(hours=i),
                'temperature': round(base_temp + np.random.normal(0, 2), 1),
                'humidity': round(60 + np.random.normal(0, 10), 1),
                'pressure': round(1013 + np.random.normal(0, 5), 1),
                'wind_speed': round(abs(np.random.normal(5, 2)), 1),
                'conditions': np.random.choice(['Clear', 'Clouds', 'Rain', 'Partly Cloudy'])
            })
        
        return pd.DataFrame(forecast)
    
    def calculate_weather_impact(self, temperature, humidity=None):
        """
        Calculate weather impact on energy demand
        Based on temperature deviation from comfort zone (18-24°C)
        """
        comfort_zone = (18, 24)
        
        if temperature < comfort_zone[0]:
            # Cold weather - heating demand
            impact = (comfort_zone[0] - temperature) * 80  # MW per degree
        elif temperature > comfort_zone[1]:
            # Hot weather - cooling demand
            impact = (temperature - comfort_zone[1]) * 100  # MW per degree
        else:
            # Comfortable temperature - minimal impact
            impact = 0
        
        # Humidity adjustment (optional)
        if humidity is not None:
            if humidity > 70:
                impact *= 1.1  # High humidity increases cooling demand
            elif humidity < 30:
                impact *= 1.05  # Low humidity increases heating demand
        
        return round(impact, 2)

if __name__ == "__main__":
    # Test weather API
    weather = WeatherAPI(location="New York")
    
    print("Current Weather:")
    current = weather.get_current_weather()
    for key, value in current.items():
        print(f"  {key}: {value}")
    
    print("\nWeather Impact on Energy Demand:")
    impact = weather.calculate_weather_impact(
        current['temperature'], 
        current['humidity']
    )
    print(f"  Additional load: {impact} MW")
    
    print("\n24-Hour Forecast:")
    forecast = weather.get_forecast(24)
    print(forecast.head())
