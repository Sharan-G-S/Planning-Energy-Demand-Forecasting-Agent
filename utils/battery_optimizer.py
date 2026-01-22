"""
Battery Storage Optimization Module
Optimizes battery energy storage systems for grid applications
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class BatteryStorageOptimizer:
    def __init__(self, capacity_mwh=100, power_rating_mw=50, efficiency=0.9):
        """
        Initialize battery storage optimizer
        capacity_mwh: total energy capacity in MWh
        power_rating_mw: maximum charge/discharge power in MW
        efficiency: round-trip efficiency (0-1)
        """
        self.capacity_mwh = capacity_mwh
        self.power_rating_mw = power_rating_mw
        self.efficiency = efficiency
        self.current_soc = 0.5  # State of Charge (50%)
        self.min_soc = 0.1  # Minimum 10%
        self.max_soc = 0.9  # Maximum 90%
        
    def optimize_charging_schedule(self, demand_forecast, price_forecast=None):
        """
        Optimize battery charging/discharging schedule
        demand_forecast: DataFrame with predicted demand
        price_forecast: DataFrame with electricity prices (optional)
        """
        schedule = []
        current_soc = self.current_soc
        
        for idx, row in demand_forecast.iterrows():
            hour = row['timestamp'].hour if 'timestamp' in row else idx
            demand = row.get('predicted_demand', row.get('energy_demand', 5000))
            
            # Determine action based on time and demand
            action = self._determine_action(hour, demand, current_soc, price_forecast)
            
            # Calculate power and energy
            if action == 'charge':
                power = min(self.power_rating_mw, 
                           (self.max_soc - current_soc) * self.capacity_mwh)
                energy = power * self.efficiency
                new_soc = min(self.max_soc, current_soc + (energy / self.capacity_mwh))
            elif action == 'discharge':
                power = min(self.power_rating_mw,
                           (current_soc - self.min_soc) * self.capacity_mwh)
                energy = power / self.efficiency
                new_soc = max(self.min_soc, current_soc - (energy / self.capacity_mwh))
            else:  # idle
                power = 0
                energy = 0
                new_soc = current_soc
            
            schedule.append({
                'hour': hour,
                'action': action,
                'power_mw': round(power, 2),
                'energy_mwh': round(energy, 2),
                'soc_before': round(current_soc * 100, 1),
                'soc_after': round(new_soc * 100, 1),
                'grid_impact': round(-power if action == 'discharge' else power, 2)
            })
            
            current_soc = new_soc
        
        return pd.DataFrame(schedule)
    
    def _determine_action(self, hour, demand, soc, price_forecast=None):
        """Determine whether to charge, discharge, or idle"""
        # Off-peak hours (low demand) - charge
        if hour in [0, 1, 2, 3, 4, 5] and soc < self.max_soc:
            return 'charge'
        
        # Peak hours (high demand) - discharge
        elif hour in [17, 18, 19, 20, 21] and soc > self.min_soc:
            return 'discharge'
        
        # Mid-day (potential solar) - charge if low SOC
        elif hour in [11, 12, 13, 14] and soc < 0.6:
            return 'charge'
        
        # Otherwise idle
        else:
            return 'idle'
    
    def calculate_peak_shaving_benefit(self, demand_forecast):
        """Calculate benefit of using battery for peak shaving"""
        schedule = self.optimize_charging_schedule(demand_forecast)
        
        # Calculate peak reduction
        discharge_hours = schedule[schedule['action'] == 'discharge']
        total_peak_reduction = discharge_hours['power_mw'].sum()
        
        benefit = {
            'peak_reduction_mw': round(total_peak_reduction, 2),
            'energy_discharged_mwh': round(discharge_hours['energy_mwh'].sum(), 2),
            'energy_charged_mwh': round(schedule[schedule['action'] == 'charge']['energy_mwh'].sum(), 2),
            'round_trip_loss_mwh': 0,
            'cost_savings': 0,
            'demand_charge_reduction': 0
        }
        
        # Calculate losses
        benefit['round_trip_loss_mwh'] = round(
            benefit['energy_charged_mwh'] - benefit['energy_discharged_mwh'], 2
        )
        
        # Estimate cost savings (simplified)
        benefit['cost_savings'] = round(total_peak_reduction * 50, 2)  # $50/MW peak reduction
        benefit['demand_charge_reduction'] = round(total_peak_reduction * 10, 2)  # $10/MW
        
        return benefit
    
    def calculate_arbitrage_potential(self, price_forecast):
        """
        Calculate revenue potential from energy arbitrage
        price_forecast: DataFrame with electricity prices
        """
        if price_forecast is None or len(price_forecast) == 0:
            # Use default price profile
            price_forecast = self._generate_default_prices(24)
        
        arbitrage = {
            'buy_energy_mwh': 0,
            'sell_energy_mwh': 0,
            'buy_cost': 0,
            'sell_revenue': 0,
            'net_revenue': 0,
            'efficiency_loss': 0
        }
        
        # Find low and high price hours
        avg_price = price_forecast['price'].mean()
        low_price_hours = price_forecast[price_forecast['price'] < avg_price * 0.8]
        high_price_hours = price_forecast[price_forecast['price'] > avg_price * 1.2]
        
        # Calculate potential arbitrage
        max_charge = min(len(low_price_hours), self.capacity_mwh / self.power_rating_mw)
        max_discharge = min(len(high_price_hours), self.capacity_mwh / self.power_rating_mw)
        
        energy_traded = min(max_charge, max_discharge) * self.power_rating_mw
        
        arbitrage['buy_energy_mwh'] = round(energy_traded, 2)
        arbitrage['sell_energy_mwh'] = round(energy_traded * self.efficiency, 2)
        arbitrage['buy_cost'] = round(energy_traded * low_price_hours['price'].mean(), 2)
        arbitrage['sell_revenue'] = round(arbitrage['sell_energy_mwh'] * high_price_hours['price'].mean(), 2)
        arbitrage['net_revenue'] = round(arbitrage['sell_revenue'] - arbitrage['buy_cost'], 2)
        arbitrage['efficiency_loss'] = round(energy_traded * (1 - self.efficiency), 2)
        
        return arbitrage
    
    def _generate_default_prices(self, hours):
        """Generate default electricity price profile"""
        prices = []
        for h in range(hours):
            if h in [0, 1, 2, 3, 4, 5]:
                price = 30  # Off-peak
            elif h in [17, 18, 19, 20, 21]:
                price = 80  # Peak
            else:
                price = 50  # Mid-peak
            
            prices.append({'hour': h, 'price': price + np.random.uniform(-5, 5)})
        
        return pd.DataFrame(prices)
    
    def calculate_frequency_regulation_value(self):
        """Calculate value from providing frequency regulation services"""
        regulation = {
            'available_capacity_mw': self.power_rating_mw,
            'response_time_seconds': 1,  # Fast response
            'annual_revenue_potential': 0,
            'capacity_payment': 0,
            'performance_payment': 0
        }
        
        # Simplified revenue calculation
        regulation['capacity_payment'] = round(self.power_rating_mw * 365 * 5, 2)  # $5/MW/day
        regulation['performance_payment'] = round(self.power_rating_mw * 365 * 3, 2)  # $3/MW/day
        regulation['annual_revenue_potential'] = round(
            regulation['capacity_payment'] + regulation['performance_payment'], 2
        )
        
        return regulation
    
    def get_battery_status(self):
        """Get current battery status"""
        return {
            'capacity_mwh': self.capacity_mwh,
            'power_rating_mw': self.power_rating_mw,
            'current_soc_percent': round(self.current_soc * 100, 1),
            'available_energy_mwh': round(self.current_soc * self.capacity_mwh, 2),
            'available_charge_capacity_mwh': round((self.max_soc - self.current_soc) * self.capacity_mwh, 2),
            'efficiency_percent': round(self.efficiency * 100, 1),
            'usable_capacity_mwh': round((self.max_soc - self.min_soc) * self.capacity_mwh, 2)
        }
    
    def simulate_operation(self, demand_forecast, days=1):
        """Simulate battery operation over multiple days"""
        results = {
            'total_energy_charged': 0,
            'total_energy_discharged': 0,
            'total_cycles': 0,
            'peak_shaving_events': 0,
            'average_soc': 0,
            'efficiency_achieved': 0
        }
        
        schedule = self.optimize_charging_schedule(demand_forecast)
        
        results['total_energy_charged'] = float(schedule[schedule['action'] == 'charge']['energy_mwh'].sum())
        results['total_energy_discharged'] = float(schedule[schedule['action'] == 'discharge']['energy_mwh'].sum())
        results['total_cycles'] = round(results['total_energy_discharged'] / self.capacity_mwh, 2)
        results['peak_shaving_events'] = len(schedule[schedule['action'] == 'discharge'])
        results['average_soc'] = round(schedule['soc_after'].mean(), 1)
        
        if results['total_energy_charged'] > 0:
            results['efficiency_achieved'] = round(
                (results['total_energy_discharged'] / results['total_energy_charged']) * 100, 2
            )
        
        return results

if __name__ == "__main__":
    # Test battery storage optimizer
    from utils.data_generator import EnergyDataGenerator
    
    print("Testing Battery Storage Optimizer...")
    
    optimizer = BatteryStorageOptimizer(capacity_mwh=100, power_rating_mw=50)
    
    # Get status
    status = optimizer.get_battery_status()
    print("\nBattery Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Generate demand forecast
    generator = EnergyDataGenerator(days=1)
    demand_data = generator.generate_data()
    
    # Optimize schedule
    schedule = optimizer.optimize_charging_schedule(demand_data)
    print(f"\n24-Hour Operation Schedule:")
    print(f"  Charge hours: {len(schedule[schedule['action'] == 'charge'])}")
    print(f"  Discharge hours: {len(schedule[schedule['action'] == 'discharge'])}")
    print(f"  Idle hours: {len(schedule[schedule['action'] == 'idle'])}")
    
    # Peak shaving benefit
    benefit = optimizer.calculate_peak_shaving_benefit(demand_data)
    print(f"\nPeak Shaving Benefit:")
    print(f"  Peak Reduction: {benefit['peak_reduction_mw']:.2f} MW")
    print(f"  Cost Savings: ${benefit['cost_savings']:.2f}")
    
    # Arbitrage potential
    arbitrage = optimizer.calculate_arbitrage_potential(None)
    print(f"\nArbitrage Potential:")
    print(f"  Net Revenue: ${arbitrage['net_revenue']:.2f}")
    
    # Frequency regulation
    regulation = optimizer.calculate_frequency_regulation_value()
    print(f"\nFrequency Regulation:")
    print(f"  Annual Revenue: ${regulation['annual_revenue_potential']:.2f}")
