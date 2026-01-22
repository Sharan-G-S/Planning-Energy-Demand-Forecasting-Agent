"""
Distributed Energy Resource (DER) Management Module
Manages solar, wind, storage, and other distributed resources
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class DERManager:
    def __init__(self):
        """Initialize DER management system"""
        self.resources = {
            'solar': {'capacity_mw': 50, 'type': 'solar'},
            'wind': {'capacity_mw': 30, 'type': 'wind'},
            'battery': {'capacity_mwh': 100, 'power_mw': 50, 'type': 'storage'},
            'diesel_gen': {'capacity_mw': 20, 'type': 'backup'}
        }
        
    def predict_solar_generation(self, hours_ahead=24):
        """Predict solar PV generation"""
        predictions = []
        current_time = datetime.now()
        
        for i in range(hours_ahead):
            timestamp = current_time + timedelta(hours=i)
            hour = timestamp.hour
            month = timestamp.month
            
            # Solar generation pattern (0 at night, peak at noon)
            if 6 <= hour <= 18:
                # Base generation curve
                solar_factor = np.sin((hour - 6) * np.pi / 12)
                
                # Seasonal adjustment
                seasonal_factor = 0.7 + 0.3 * np.sin((month - 3) * np.pi / 6)
                
                # Cloud cover (random)
                cloud_factor = np.random.uniform(0.7, 1.0)
                
                generation = (self.resources['solar']['capacity_mw'] * 
                            solar_factor * seasonal_factor * cloud_factor)
            else:
                generation = 0
            
            predictions.append({
                'timestamp': timestamp,
                'solar_generation_mw': round(generation, 2),
                'capacity_factor': round(generation / self.resources['solar']['capacity_mw'] * 100, 1) if generation > 0 else 0
            })
        
        return pd.DataFrame(predictions)
    
    def predict_wind_generation(self, hours_ahead=24):
        """Predict wind turbine generation"""
        predictions = []
        current_time = datetime.now()
        
        for i in range(hours_ahead):
            timestamp = current_time + timedelta(hours=i)
            hour = timestamp.hour
            
            # Wind generation (more variable than solar)
            base_wind = np.random.uniform(0.3, 0.9)
            
            # Diurnal pattern (typically higher at night)
            if 0 <= hour <= 6 or 20 <= hour <= 23:
                wind_factor = 1.2
            else:
                wind_factor = 0.8
            
            generation = (self.resources['wind']['capacity_mw'] * 
                         base_wind * wind_factor)
            
            predictions.append({
                'timestamp': timestamp,
                'wind_generation_mw': round(generation, 2),
                'capacity_factor': round(generation / self.resources['wind']['capacity_mw'] * 100, 1)
            })
        
        return pd.DataFrame(predictions)
    
    def aggregate_der_forecast(self, hours_ahead=24):
        """Aggregate all DER forecasts"""
        solar = self.predict_solar_generation(hours_ahead)
        wind = self.predict_wind_generation(hours_ahead)
        
        # Combine forecasts
        aggregate = pd.DataFrame({
            'timestamp': solar['timestamp'],
            'solar_mw': solar['solar_generation_mw'],
            'wind_mw': wind['wind_generation_mw'],
            'total_renewable_mw': solar['solar_generation_mw'] + wind['wind_generation_mw'],
            'battery_available_mw': self.resources['battery']['power_mw'],
            'backup_available_mw': self.resources['diesel_gen']['capacity_mw']
        })
        
        return aggregate
    
    def optimize_der_dispatch(self, demand_forecast, der_forecast):
        """
        Optimize dispatch of distributed energy resources
        """
        dispatch_schedule = []
        
        for idx in range(len(demand_forecast)):
            demand = demand_forecast.iloc[idx]['predicted_demand'] if 'predicted_demand' in demand_forecast.columns else demand_forecast.iloc[idx]['energy_demand']
            solar = der_forecast.iloc[idx]['solar_mw']
            wind = der_forecast.iloc[idx]['wind_mw']
            
            # Calculate net demand after renewables
            net_demand = demand - solar - wind
            
            # Determine resource dispatch
            if net_demand > 0:
                # Need additional power
                battery_dispatch = min(net_demand, self.resources['battery']['power_mw'])
                remaining = net_demand - battery_dispatch
                backup_dispatch = min(remaining, self.resources['diesel_gen']['capacity_mw'])
                grid_import = max(0, remaining - backup_dispatch)
            else:
                # Excess renewable energy
                battery_charge = min(abs(net_demand), self.resources['battery']['power_mw'])
                curtailment = max(0, abs(net_demand) - battery_charge)
                battery_dispatch = -battery_charge  # Negative = charging
                backup_dispatch = 0
                grid_import = 0
            
            dispatch_schedule.append({
                'hour': idx,
                'demand_mw': round(demand, 2),
                'solar_mw': round(solar, 2),
                'wind_mw': round(wind, 2),
                'battery_mw': round(battery_dispatch, 2),
                'backup_mw': round(backup_dispatch, 2) if net_demand > 0 else 0,
                'grid_import_mw': round(grid_import, 2) if net_demand > 0 else 0,
                'curtailment_mw': round(curtailment, 2) if net_demand < 0 else 0,
                'renewable_penetration': round((solar + wind) / demand * 100, 1) if demand > 0 else 0
            })
        
        return pd.DataFrame(dispatch_schedule)
    
    def calculate_der_benefits(self, dispatch_schedule):
        """Calculate benefits of DER integration"""
        benefits = {
            'renewable_energy_mwh': 0,
            'grid_import_reduction_mwh': 0,
            'backup_fuel_saved': 0,
            'co2_reduction_tons': 0,
            'cost_savings': 0,
            'renewable_penetration_avg': 0,
            'self_sufficiency_ratio': 0
        }
        
        # Calculate totals
        benefits['renewable_energy_mwh'] = round(
            (dispatch_schedule['solar_mw'] + dispatch_schedule['wind_mw']).sum(), 2
        )
        
        total_demand = dispatch_schedule['demand_mw'].sum()
        benefits['grid_import_reduction_mwh'] = round(
            total_demand - dispatch_schedule['grid_import_mw'].sum(), 2
        )
        
        # Environmental benefits
        benefits['co2_reduction_tons'] = round(benefits['renewable_energy_mwh'] * 0.5, 2)  # 0.5 tons/MWh
        
        # Economic benefits
        benefits['cost_savings'] = round(benefits['renewable_energy_mwh'] * 60, 2)  # $60/MWh avoided
        
        # Performance metrics
        benefits['renewable_penetration_avg'] = round(
            dispatch_schedule['renewable_penetration'].mean(), 1
        )
        
        if total_demand > 0:
            benefits['self_sufficiency_ratio'] = round(
                (1 - dispatch_schedule['grid_import_mw'].sum() / total_demand) * 100, 1
            )
        
        return benefits
    
    def identify_der_expansion_opportunities(self, dispatch_schedule):
        """Identify opportunities for DER expansion"""
        opportunities = []
        
        # Check for high grid import hours
        high_import = dispatch_schedule[dispatch_schedule['grid_import_mw'] > 100]
        if len(high_import) > 0:
            opportunities.append({
                'type': 'battery_expansion',
                'reason': f'{len(high_import)} hours with high grid import',
                'recommended_capacity': round(high_import['grid_import_mw'].mean(), 2),
                'estimated_benefit': 'Reduce peak demand charges'
            })
        
        # Check for curtailment
        curtailed = dispatch_schedule[dispatch_schedule['curtailment_mw'] > 0]
        if len(curtailed) > 0:
            opportunities.append({
                'type': 'storage_expansion',
                'reason': f'{curtailed["curtailment_mw"].sum():.2f} MWh curtailed',
                'recommended_capacity': round(curtailed['curtailment_mw'].mean() * 4, 2),
                'estimated_benefit': 'Capture excess renewable energy'
            })
        
        # Check renewable penetration
        avg_penetration = dispatch_schedule['renewable_penetration'].mean()
        if avg_penetration < 50:
            opportunities.append({
                'type': 'renewable_expansion',
                'reason': f'Current penetration only {avg_penetration:.1f}%',
                'recommended_capacity': round(self.resources['solar']['capacity_mw'] * 0.5, 2),
                'estimated_benefit': 'Increase renewable energy usage'
            })
        
        return opportunities
    
    def get_der_portfolio_summary(self):
        """Get summary of DER portfolio"""
        return {
            'total_renewable_capacity_mw': self.resources['solar']['capacity_mw'] + self.resources['wind']['capacity_mw'],
            'solar_capacity_mw': self.resources['solar']['capacity_mw'],
            'wind_capacity_mw': self.resources['wind']['capacity_mw'],
            'battery_capacity_mwh': self.resources['battery']['capacity_mwh'],
            'battery_power_mw': self.resources['battery']['power_mw'],
            'backup_capacity_mw': self.resources['diesel_gen']['capacity_mw'],
            'total_resources': len(self.resources)
        }

if __name__ == "__main__":
    # Test DER manager
    from utils.data_generator import EnergyDataGenerator
    
    print("Testing DER Manager...")
    
    manager = DERManager()
    
    # Get portfolio summary
    portfolio = manager.get_der_portfolio_summary()
    print("\nDER Portfolio:")
    for key, value in portfolio.items():
        print(f"  {key}: {value}")
    
    # Generate forecasts
    solar_forecast = manager.predict_solar_generation(24)
    wind_forecast = manager.predict_wind_generation(24)
    der_forecast = manager.aggregate_der_forecast(24)
    
    print(f"\n24-Hour Renewable Forecast:")
    print(f"  Solar: {solar_forecast['solar_generation_mw'].sum():.2f} MWh")
    print(f"  Wind: {wind_forecast['wind_generation_mw'].sum():.2f} MWh")
    print(f"  Total: {der_forecast['total_renewable_mw'].sum():.2f} MWh")
    
    # Generate demand forecast
    generator = EnergyDataGenerator(days=1)
    demand_data = generator.generate_data()
    
    # Optimize dispatch
    dispatch = manager.optimize_der_dispatch(demand_data, der_forecast)
    print(f"\nDispatch Optimization:")
    print(f"  Avg Renewable Penetration: {dispatch['renewable_penetration'].mean():.1f}%")
    print(f"  Grid Import: {dispatch['grid_import_mw'].sum():.2f} MWh")
    print(f"  Curtailment: {dispatch['curtailment_mw'].sum():.2f} MWh")
    
    # Calculate benefits
    benefits = manager.calculate_der_benefits(dispatch)
    print(f"\nDER Benefits:")
    print(f"  Renewable Energy: {benefits['renewable_energy_mwh']:.2f} MWh")
    print(f"  CO2 Reduction: {benefits['co2_reduction_tons']:.2f} tons")
    print(f"  Cost Savings: ${benefits['cost_savings']:.2f}")
    print(f"  Self-Sufficiency: {benefits['self_sufficiency_ratio']:.1f}%")
    
    # Expansion opportunities
    opportunities = manager.identify_der_expansion_opportunities(dispatch)
    print(f"\nExpansion Opportunities: {len(opportunities)}")
    for opp in opportunities:
        print(f"  {opp['type']}: {opp['reason']}")
