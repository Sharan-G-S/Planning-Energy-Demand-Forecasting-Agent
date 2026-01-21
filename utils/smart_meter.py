"""
Smart Meter Data Integration
Simulates real-time smart meter data collection and processing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SmartMeterData:
    def __init__(self, num_meters=1000):
        """
        Initialize smart meter data collector
        In production, this would connect to actual smart meter infrastructure
        """
        self.num_meters = num_meters
        self.meter_ids = [f"METER_{i:05d}" for i in range(num_meters)]
        
    def get_real_time_readings(self):
        """
        Get current readings from all smart meters
        Simulates real-time data collection
        """
        readings = []
        current_time = datetime.now()
        
        # Simulate readings from all meters
        for meter_id in self.meter_ids:
            # Base consumption varies by meter type (residential/commercial)
            is_commercial = np.random.random() > 0.7
            base_consumption = np.random.uniform(2, 5) if not is_commercial else np.random.uniform(10, 50)
            
            # Time-of-day variation
            hour = current_time.hour
            time_factor = 1 + 0.5 * np.sin((hour - 6) * np.pi / 12)
            
            # Random variation
            consumption = base_consumption * time_factor * np.random.uniform(0.8, 1.2)
            
            readings.append({
                'meter_id': meter_id,
                'timestamp': current_time,
                'consumption_kw': round(consumption, 2),
                'voltage': round(np.random.uniform(230, 240), 1),
                'power_factor': round(np.random.uniform(0.85, 0.95), 2),
                'meter_type': 'commercial' if is_commercial else 'residential'
            })
        
        return pd.DataFrame(readings)
    
    def aggregate_consumption(self, readings_df=None):
        """
        Aggregate smart meter data to total grid consumption
        """
        if readings_df is None:
            readings_df = self.get_real_time_readings()
        
        total_consumption = readings_df['consumption_kw'].sum() / 1000  # Convert to MW
        
        return {
            'total_consumption_mw': round(total_consumption, 2),
            'num_meters': len(readings_df),
            'avg_consumption_kw': round(readings_df['consumption_kw'].mean(), 2),
            'peak_consumption_kw': round(readings_df['consumption_kw'].max(), 2),
            'timestamp': readings_df['timestamp'].iloc[0],
            'residential_consumption': round(
                readings_df[readings_df['meter_type'] == 'residential']['consumption_kw'].sum() / 1000, 2
            ),
            'commercial_consumption': round(
                readings_df[readings_df['meter_type'] == 'commercial']['consumption_kw'].sum() / 1000, 2
            )
        }
    
    def get_historical_patterns(self, days=30):
        """
        Analyze historical smart meter data for patterns
        """
        patterns = {
            'peak_hours': [18, 19, 20],  # 6-8 PM
            'low_hours': [2, 3, 4],      # 2-4 AM
            'weekday_avg': np.random.uniform(5000, 6000),
            'weekend_avg': np.random.uniform(4000, 5000),
            'growth_rate': 0.02  # 2% annual growth
        }
        
        return patterns
    
    def detect_meter_anomalies(self, readings_df=None):
        """
        Detect anomalies in smart meter readings
        """
        if readings_df is None:
            readings_df = self.get_real_time_readings()
        
        anomalies = []
        
        # Detect unusually high consumption
        mean_consumption = readings_df['consumption_kw'].mean()
        std_consumption = readings_df['consumption_kw'].std()
        
        high_consumption = readings_df[
            readings_df['consumption_kw'] > mean_consumption + 3 * std_consumption
        ]
        
        for _, row in high_consumption.iterrows():
            anomalies.append({
                'meter_id': row['meter_id'],
                'type': 'high_consumption',
                'value': row['consumption_kw'],
                'expected': mean_consumption,
                'severity': 'high'
            })
        
        # Detect voltage issues
        voltage_issues = readings_df[
            (readings_df['voltage'] < 220) | (readings_df['voltage'] > 250)
        ]
        
        for _, row in voltage_issues.iterrows():
            anomalies.append({
                'meter_id': row['meter_id'],
                'type': 'voltage_anomaly',
                'value': row['voltage'],
                'expected': 230,
                'severity': 'medium'
            })
        
        return anomalies
    
    def generate_load_profile(self, meter_id, hours=24):
        """
        Generate load profile for a specific meter
        """
        profile = []
        base_time = datetime.now()
        
        for i in range(hours):
            hour = (base_time + timedelta(hours=i)).hour
            
            # Residential pattern
            if hour < 6:
                load = np.random.uniform(1, 2)
            elif 6 <= hour < 9:
                load = np.random.uniform(3, 5)
            elif 9 <= hour < 17:
                load = np.random.uniform(2, 3)
            elif 17 <= hour < 22:
                load = np.random.uniform(4, 6)
            else:
                load = np.random.uniform(2, 3)
            
            profile.append({
                'timestamp': base_time + timedelta(hours=i),
                'consumption_kw': round(load, 2)
            })
        
        return pd.DataFrame(profile)

if __name__ == "__main__":
    # Test smart meter data
    smart_meters = SmartMeterData(num_meters=1000)
    
    print("Real-time Smart Meter Readings:")
    readings = smart_meters.get_real_time_readings()
    print(readings.head())
    
    print("\nAggregated Consumption:")
    aggregated = smart_meters.aggregate_consumption(readings)
    for key, value in aggregated.items():
        print(f"  {key}: {value}")
    
    print("\nMeter Anomalies:")
    anomalies = smart_meters.detect_meter_anomalies(readings)
    print(f"  Found {len(anomalies)} anomalies")
    if anomalies:
        print(f"  Example: {anomalies[0]}")
