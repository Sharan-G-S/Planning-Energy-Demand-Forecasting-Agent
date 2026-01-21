"""
Grid Optimization and Load Balancing
"""

import numpy as np
import pandas as pd
import config

class GridOptimizer:
    def __init__(self, max_capacity=config.MAX_GRID_CAPACITY):
        self.max_capacity = max_capacity
        self.peak_threshold = config.PEAK_THRESHOLD
        self.optimal_range = config.OPTIMAL_LOAD_RANGE
        
    def calculate_load_factor(self, demand):
        """Calculate current load factor (0-1)"""
        return demand / self.max_capacity
    
    def identify_peak_hours(self, forecast_df):
        """Identify hours with peak demand"""
        forecast_df['load_factor'] = forecast_df['predicted_demand'] / self.max_capacity
        peak_hours = forecast_df[forecast_df['load_factor'] > self.peak_threshold].copy()
        return peak_hours
    
    def calculate_load_shift_potential(self, forecast_df):
        """Calculate potential for load shifting"""
        forecast_df['load_factor'] = forecast_df['predicted_demand'] / self.max_capacity
        
        # Find hours above and below optimal range
        high_load = forecast_df[forecast_df['load_factor'] > self.optimal_range[1]]
        low_load = forecast_df[forecast_df['load_factor'] < self.optimal_range[0]]
        
        # Calculate shiftable load
        excess_load = high_load['predicted_demand'].sum() - (self.optimal_range[1] * self.max_capacity * len(high_load))
        available_capacity = (self.optimal_range[1] * self.max_capacity * len(low_load)) - low_load['predicted_demand'].sum()
        
        shiftable = min(excess_load, available_capacity)
        
        return {
            'shiftable_load_mw': round(shiftable, 2),
            'high_load_hours': len(high_load),
            'low_load_hours': len(low_load),
            'potential_savings_percent': round((shiftable / forecast_df['predicted_demand'].sum()) * 100, 2)
        }
    
    def generate_recommendations(self, forecast_df):
        """Generate grid optimization recommendations"""
        recommendations = []
        
        # Identify peak hours
        peak_hours = self.identify_peak_hours(forecast_df)
        
        if len(peak_hours) > 0:
            recommendations.append({
                'type': 'peak_management',
                'priority': 'high',
                'title': 'Peak Demand Alert',
                'description': f'{len(peak_hours)} hours forecasted above {int(self.peak_threshold*100)}% capacity',
                'action': 'Implement demand response programs or activate reserve capacity',
                'affected_hours': peak_hours['timestamp'].tolist() if 'timestamp' in peak_hours.columns else [],
                'estimated_impact': f'{int(peak_hours["load_factor"].max()*100)}% peak load'
            })
        
        # Load shifting opportunities
        shift_potential = self.calculate_load_shift_potential(forecast_df)
        if shift_potential['shiftable_load_mw'] > 100:
            recommendations.append({
                'type': 'load_shifting',
                'priority': 'medium',
                'title': 'Load Shifting Opportunity',
                'description': f'{shift_potential["shiftable_load_mw"]} MW can be shifted to off-peak hours',
                'action': 'Encourage flexible loads to shift to low-demand periods',
                'estimated_impact': f'{shift_potential["potential_savings_percent"]}% efficiency gain'
            })
        
        # Renewable energy integration
        avg_load = forecast_df['predicted_demand'].mean()
        if avg_load < self.max_capacity * 0.6:
            recommendations.append({
                'type': 'renewable_integration',
                'priority': 'low',
                'title': 'Renewable Energy Opportunity',
                'description': 'Average load allows for increased renewable energy integration',
                'action': 'Maximize solar/wind generation during low-demand periods',
                'estimated_impact': 'Up to 30% renewable energy penetration possible'
            })
        
        # Grid stability
        load_variance = forecast_df['predicted_demand'].std()
        if load_variance > 1000:
            recommendations.append({
                'type': 'stability',
                'priority': 'medium',
                'title': 'Load Variance Alert',
                'description': 'High variance in predicted demand may affect grid stability',
                'action': 'Prepare spinning reserves and frequency regulation',
                'estimated_impact': f'{round(load_variance, 0)} MW standard deviation'
            })
        
        return recommendations
    
    def calculate_cost_optimization(self, forecast_df, peak_rate=0.15, off_peak_rate=0.08):
        """Calculate potential cost savings through optimization"""
        forecast_df['load_factor'] = forecast_df['predicted_demand'] / self.max_capacity
        
        # Current cost (assuming peak rates during high load)
        forecast_df['rate'] = forecast_df['load_factor'].apply(
            lambda x: peak_rate if x > self.optimal_range[1] else off_peak_rate
        )
        current_cost = (forecast_df['predicted_demand'] * forecast_df['rate']).sum()
        
        # Optimized cost (with load shifting)
        shift_potential = self.calculate_load_shift_potential(forecast_df)
        optimized_cost = current_cost * (1 - shift_potential['potential_savings_percent'] / 100)
        
        return {
            'current_cost': round(current_cost, 2),
            'optimized_cost': round(optimized_cost, 2),
            'potential_savings': round(current_cost - optimized_cost, 2),
            'savings_percent': round(((current_cost - optimized_cost) / current_cost) * 100, 2)
        }
    
    def get_grid_status(self, current_demand):
        """Get current grid status"""
        load_factor = self.calculate_load_factor(current_demand)
        
        if load_factor > self.peak_threshold:
            status = 'critical'
            message = 'Grid operating near capacity - implement demand response'
        elif load_factor > self.optimal_range[1]:
            status = 'high'
            message = 'High load - monitor closely'
        elif load_factor < self.optimal_range[0]:
            status = 'low'
            message = 'Low load - opportunity for maintenance or renewable integration'
        else:
            status = 'optimal'
            message = 'Grid operating in optimal range'
        
        return {
            'status': status,
            'load_factor': round(load_factor, 3),
            'current_demand': round(current_demand, 2),
            'available_capacity': round(self.max_capacity - current_demand, 2),
            'message': message
        }

if __name__ == "__main__":
    # Test grid optimizer
    optimizer = GridOptimizer()
    
    # Create sample forecast
    forecast = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=24, freq='H'),
        'predicted_demand': np.random.uniform(4000, 9000, 24)
    })
    
    recommendations = optimizer.generate_recommendations(forecast)
    print("Grid Optimization Recommendations:")
    for rec in recommendations:
        print(f"\n{rec['title']} ({rec['priority']} priority)")
        print(f"  {rec['description']}")
        print(f"  Action: {rec['action']}")
