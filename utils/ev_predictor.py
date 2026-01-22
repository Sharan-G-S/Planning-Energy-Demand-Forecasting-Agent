"""
Electric Vehicle (EV) Load Prediction Module
Predicts charging demand from electric vehicles
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class EVLoadPredictor:
    def __init__(self, num_evs=5000, avg_battery_capacity=60):
        """
        Initialize EV load predictor
        num_evs: number of electric vehicles in the grid
        avg_battery_capacity: average battery capacity in kWh
        """
        self.num_evs = num_evs
        self.avg_battery_capacity = avg_battery_capacity
        self.charging_profiles = self._initialize_charging_profiles()
        
    def _initialize_charging_profiles(self):
        """Initialize different EV charging profiles"""
        return {
            'home_charging': {
                'power': 7.2,  # kW (Level 2)
                'peak_hours': [18, 19, 20, 21, 22, 23],
                'probability': 0.7
            },
            'work_charging': {
                'power': 7.2,  # kW (Level 2)
                'peak_hours': [8, 9, 10, 11, 12, 13, 14, 15],
                'probability': 0.2
            },
            'fast_charging': {
                'power': 50,  # kW (DC Fast Charging)
                'peak_hours': [12, 13, 17, 18],
                'probability': 0.1
            }
        }
    
    def predict_ev_load(self, hours_ahead=24):
        """Predict EV charging load for next N hours"""
        predictions = []
        current_time = datetime.now()
        
        for i in range(hours_ahead):
            timestamp = current_time + timedelta(hours=i)
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Calculate charging demand
            total_load = 0
            
            for profile_name, profile in self.charging_profiles.items():
                # Check if this is a peak hour for this profile
                if hour in profile['peak_hours']:
                    # Calculate number of EVs charging
                    num_charging = int(self.num_evs * profile['probability'])
                    
                    # Adjust for weekends (less work charging)
                    if day_of_week >= 5 and profile_name == 'work_charging':
                        num_charging = int(num_charging * 0.3)
                    
                    # Calculate load
                    load = num_charging * profile['power']
                    total_load += load
            
            # Add random variation
            total_load *= np.random.uniform(0.85, 1.15)
            
            predictions.append({
                'timestamp': timestamp,
                'ev_load_kw': round(total_load, 2),
                'ev_load_mw': round(total_load / 1000, 2),
                'num_charging_estimated': int(total_load / 7.2),
                'charging_rate': self._get_charging_rate(hour)
            })
        
        return pd.DataFrame(predictions)
    
    def _get_charging_rate(self, hour):
        """Get charging rate category for the hour"""
        if hour in [18, 19, 20, 21, 22, 23]:
            return 'peak'
        elif hour in [0, 1, 2, 3, 4, 5]:
            return 'off-peak'
        else:
            return 'mid-peak'
    
    def optimize_ev_charging(self, forecast_df, grid_capacity=10000):
        """
        Optimize EV charging schedule to minimize grid impact
        """
        optimization = {
            'current_schedule': [],
            'optimized_schedule': [],
            'load_shifted': 0,
            'cost_savings': 0
        }
        
        # Identify peak and off-peak hours
        peak_hours = forecast_df[forecast_df['charging_rate'] == 'peak']
        off_peak_hours = forecast_df[forecast_df['charging_rate'] == 'off-peak']
        
        # Calculate potential load shift
        peak_load = peak_hours['ev_load_mw'].sum()
        off_peak_capacity = len(off_peak_hours) * (grid_capacity * 0.3)
        
        # Determine how much can be shifted
        shiftable_load = min(peak_load * 0.4, off_peak_capacity * 0.5)
        
        optimization['load_shifted'] = round(shiftable_load, 2)
        optimization['cost_savings'] = round(shiftable_load * 0.08, 2)  # $0.08/MWh savings
        
        # Create optimized schedule
        for _, row in forecast_df.iterrows():
            current = {
                'hour': row['timestamp'].hour,
                'load_mw': row['ev_load_mw']
            }
            optimization['current_schedule'].append(current)
            
            # Adjust for optimization
            if row['charging_rate'] == 'peak':
                optimized_load = row['ev_load_mw'] * 0.6  # Reduce by 40%
            elif row['charging_rate'] == 'off-peak':
                optimized_load = row['ev_load_mw'] * 1.3  # Increase by 30%
            else:
                optimized_load = row['ev_load_mw']
            
            optimization['optimized_schedule'].append({
                'hour': row['timestamp'].hour,
                'load_mw': round(optimized_load, 2)
            })
        
        return optimization
    
    def calculate_v2g_potential(self, connected_evs_ratio=0.3):
        """
        Calculate Vehicle-to-Grid (V2G) potential
        connected_evs_ratio: ratio of EVs connected and available for V2G
        """
        available_evs = int(self.num_evs * connected_evs_ratio)
        avg_available_energy = self.avg_battery_capacity * 0.5  # 50% available
        
        v2g_potential = {
            'available_evs': available_evs,
            'total_capacity_kwh': available_evs * avg_available_energy,
            'total_capacity_mwh': round(available_evs * avg_available_energy / 1000, 2),
            'max_discharge_power_mw': round(available_evs * 7.2 / 1000, 2),
            'duration_hours': round(avg_available_energy / 7.2, 2)
        }
        
        return v2g_potential
    
    def get_ev_statistics(self):
        """Get current EV fleet statistics"""
        return {
            'total_evs': self.num_evs,
            'avg_battery_capacity': self.avg_battery_capacity,
            'total_battery_capacity_mwh': round(self.num_evs * self.avg_battery_capacity / 1000, 2),
            'charging_profiles': list(self.charging_profiles.keys()),
            'estimated_daily_consumption_mwh': round(self.num_evs * 0.3 * self.avg_battery_capacity / 1000, 2)
        }
    
    def predict_smart_charging_impact(self, hours_ahead=24):
        """Predict impact of smart charging strategies"""
        base_forecast = self.predict_ev_load(hours_ahead)
        optimization = self.optimize_ev_charging(base_forecast)
        
        impact = {
            'base_peak_load': float(base_forecast['ev_load_mw'].max()),
            'optimized_peak_load': max([s['load_mw'] for s in optimization['optimized_schedule']]),
            'peak_reduction': 0,
            'load_shifted_mw': optimization['load_shifted'],
            'cost_savings': optimization['cost_savings'],
            'grid_impact_reduction': 0
        }
        
        impact['peak_reduction'] = round(impact['base_peak_load'] - impact['optimized_peak_load'], 2)
        impact['grid_impact_reduction'] = round((impact['peak_reduction'] / impact['base_peak_load']) * 100, 2)
        
        return impact

if __name__ == "__main__":
    # Test EV load predictor
    print("Testing EV Load Predictor...")
    
    predictor = EVLoadPredictor(num_evs=5000, avg_battery_capacity=60)
    
    # Get statistics
    stats = predictor.get_ev_statistics()
    print("\nEV Fleet Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Predict EV load
    forecast = predictor.predict_ev_load(hours_ahead=24)
    print(f"\n24-Hour EV Load Forecast:")
    print(f"  Average Load: {forecast['ev_load_mw'].mean():.2f} MW")
    print(f"  Peak Load: {forecast['ev_load_mw'].max():.2f} MW")
    print(f"  Total Energy: {forecast['ev_load_mw'].sum():.2f} MWh")
    
    # Optimize charging
    optimization = predictor.optimize_ev_charging(forecast)
    print(f"\nCharging Optimization:")
    print(f"  Load Shifted: {optimization['load_shifted']:.2f} MW")
    print(f"  Cost Savings: ${optimization['cost_savings']:.2f}")
    
    # V2G potential
    v2g = predictor.calculate_v2g_potential()
    print(f"\nV2G Potential:")
    print(f"  Available EVs: {v2g['available_evs']}")
    print(f"  Total Capacity: {v2g['total_capacity_mwh']:.2f} MWh")
    print(f"  Max Power: {v2g['max_discharge_power_mw']:.2f} MW")
    
    # Smart charging impact
    impact = predictor.predict_smart_charging_impact()
    print(f"\nSmart Charging Impact:")
    print(f"  Peak Reduction: {impact['peak_reduction']:.2f} MW ({impact['grid_impact_reduction']:.1f}%)")
    print(f"  Cost Savings: ${impact['cost_savings']:.2f}")
