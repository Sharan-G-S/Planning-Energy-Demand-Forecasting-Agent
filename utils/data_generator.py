"""
Synthetic Energy Demand Data Generator
Generates realistic energy consumption patterns with seasonal, daily, and random variations
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class EnergyDataGenerator:
    def __init__(self, days=365):
        self.days = days
        self.hours = days * 24
        
    def generate_base_load(self):
        """Generate base load pattern (average consumption)"""
        # Base load around 5000 MW with slight random variation
        base = 5000 + np.random.normal(0, 100, self.hours)
        return base
    
    def generate_daily_pattern(self):
        """Generate daily consumption pattern (higher during day, lower at night)"""
        pattern = np.zeros(self.hours)
        for i in range(self.hours):
            hour_of_day = i % 24
            # Peak during 8am-10pm, low during night
            if 6 <= hour_of_day <= 22:
                pattern[i] = 2000 * np.sin((hour_of_day - 6) * np.pi / 16)
            else:
                pattern[i] = -500
        return pattern
    
    def generate_weekly_pattern(self):
        """Generate weekly pattern (lower on weekends)"""
        pattern = np.zeros(self.hours)
        for i in range(self.hours):
            day_of_week = (i // 24) % 7
            # Lower consumption on weekends (5, 6)
            if day_of_week in [5, 6]:
                pattern[i] = -800
            else:
                pattern[i] = 400
        return pattern
    
    def generate_seasonal_pattern(self):
        """Generate seasonal pattern (higher in summer/winter for AC/heating)"""
        pattern = np.zeros(self.hours)
        for i in range(self.hours):
            day_of_year = (i // 24) % 365
            # Higher in summer (days 150-240) and winter (days 0-60, 300-365)
            seasonal_factor = np.sin(2 * np.pi * day_of_year / 365)
            pattern[i] = 1500 * abs(seasonal_factor)
        return pattern
    
    def generate_weather_impact(self):
        """Simulate weather impact on energy demand"""
        # Temperature variation affects AC/heating usage
        temperature = 20 + 15 * np.sin(np.linspace(0, 4*np.pi, self.hours))
        temperature += np.random.normal(0, 3, self.hours)
        
        # Extreme temperatures increase energy demand
        weather_load = np.zeros(self.hours)
        for i in range(self.hours):
            if temperature[i] > 30:  # Hot weather - AC usage
                weather_load[i] = (temperature[i] - 30) * 100
            elif temperature[i] < 10:  # Cold weather - heating
                weather_load[i] = (10 - temperature[i]) * 80
        
        return weather_load, temperature
    
    def generate_random_events(self):
        """Generate random spikes/drops (special events, outages)"""
        events = np.zeros(self.hours)
        num_events = int(self.hours * 0.02)  # 2% of hours have events
        
        event_indices = np.random.choice(self.hours, num_events, replace=False)
        for idx in event_indices:
            # Random spike or drop
            events[idx] = np.random.choice([-1, 1]) * np.random.uniform(500, 1500)
        
        return events
    
    def generate_data(self):
        """Generate complete synthetic energy demand dataset"""
        # Start date
        start_date = datetime.now() - timedelta(days=self.days)
        timestamps = [start_date + timedelta(hours=i) for i in range(self.hours)]
        
        # Combine all patterns
        base_load = self.generate_base_load()
        daily = self.generate_daily_pattern()
        weekly = self.generate_weekly_pattern()
        seasonal = self.generate_seasonal_pattern()
        weather_load, temperature = self.generate_weather_impact()
        events = self.generate_random_events()
        
        # Total energy demand
        energy_demand = base_load + daily + weekly + seasonal + weather_load + events
        
        # Add small random noise
        energy_demand += np.random.normal(0, 50, self.hours)
        
        # Ensure non-negative values
        energy_demand = np.maximum(energy_demand, 1000)
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'energy_demand': energy_demand,
            'temperature': temperature,
            'hour': [t.hour for t in timestamps],
            'day_of_week': [t.weekday() for t in timestamps],
            'month': [t.month for t in timestamps],
            'is_weekend': [1 if t.weekday() >= 5 else 0 for t in timestamps]
        })
        
        return df
    
    def save_data(self, filepath='data/historical_data.csv'):
        """Generate and save data to CSV"""
        df = self.generate_data()
        df.to_csv(filepath, index=False)
        print(f"Generated {len(df)} hours of data and saved to {filepath}")
        return df

if __name__ == "__main__":
    generator = EnergyDataGenerator(days=config.HISTORICAL_DAYS)
    data = generator.save_data()
    print("\nData Statistics:")
    print(data.describe())
