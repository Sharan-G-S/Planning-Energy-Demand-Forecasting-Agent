"""
Multi-Region Forecasting Module
Enables energy demand forecasting across multiple geographic regions
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from models.ensemble_predictor_simple import EnsemblePredictor

class MultiRegionForecaster:
    def __init__(self, regions=None):
        """
        Initialize multi-region forecaster
        regions: list of region names/IDs
        """
        self.regions = regions or ['North', 'South', 'East', 'West', 'Central']
        self.region_models = {}
        self.region_characteristics = {}
        
        # Initialize models for each region
        for region in self.regions:
            self.region_models[region] = EnsemblePredictor()
            self.region_characteristics[region] = self._get_region_characteristics(region)
    
    def _get_region_characteristics(self, region):
        """Get characteristics for each region"""
        characteristics = {
            'North': {
                'base_load': 6000,
                'peak_multiplier': 1.3,
                'industrial_ratio': 0.4,
                'residential_ratio': 0.6,
                'climate_factor': 'cold',
                'timezone_offset': 0
            },
            'South': {
                'base_load': 5500,
                'peak_multiplier': 1.5,
                'industrial_ratio': 0.3,
                'residential_ratio': 0.7,
                'climate_factor': 'hot',
                'timezone_offset': 0
            },
            'East': {
                'base_load': 7000,
                'peak_multiplier': 1.4,
                'industrial_ratio': 0.5,
                'residential_ratio': 0.5,
                'climate_factor': 'moderate',
                'timezone_offset': 3
            },
            'West': {
                'base_load': 6500,
                'peak_multiplier': 1.2,
                'industrial_ratio': 0.35,
                'residential_ratio': 0.65,
                'climate_factor': 'moderate',
                'timezone_offset': -3
            },
            'Central': {
                'base_load': 5000,
                'peak_multiplier': 1.25,
                'industrial_ratio': 0.45,
                'residential_ratio': 0.55,
                'climate_factor': 'moderate',
                'timezone_offset': 0
            }
        }
        return characteristics.get(region, characteristics['Central'])
    
    def train_region(self, region, historical_data):
        """Train model for specific region"""
        if region not in self.region_models:
            self.region_models[region] = EnsemblePredictor()
        
        self.region_models[region].train(historical_data)
        return True
    
    def predict_region(self, region, historical_data, hours_ahead=24):
        """Predict energy demand for specific region"""
        if region not in self.region_models:
            raise ValueError(f"Region {region} not initialized")
        
        # Get base prediction
        predictions = self.region_models[region].predict(historical_data, hours_ahead)
        
        # Apply region-specific adjustments
        char = self.region_characteristics[region]
        predictions['predicted_demand'] *= char['peak_multiplier']
        predictions['region'] = region
        
        return predictions
    
    def predict_all_regions(self, historical_data_dict, hours_ahead=24):
        """
        Predict for all regions
        historical_data_dict: {region_name: historical_df}
        """
        all_predictions = {}
        
        for region in self.regions:
            if region in historical_data_dict:
                all_predictions[region] = self.predict_region(
                    region, 
                    historical_data_dict[region], 
                    hours_ahead
                )
        
        return all_predictions
    
    def get_regional_summary(self, predictions_dict):
        """Get summary statistics across all regions"""
        summary = {
            'total_demand': 0,
            'peak_demand': 0,
            'regions': {},
            'timestamp': datetime.now()
        }
        
        for region, pred_df in predictions_dict.items():
            region_stats = {
                'avg_demand': float(pred_df['predicted_demand'].mean()),
                'peak_demand': float(pred_df['predicted_demand'].max()),
                'min_demand': float(pred_df['predicted_demand'].min())
            }
            summary['regions'][region] = region_stats
            summary['total_demand'] += region_stats['avg_demand']
            summary['peak_demand'] = max(summary['peak_demand'], region_stats['peak_demand'])
        
        return summary
    
    def identify_load_transfer_opportunities(self, predictions_dict):
        """
        Identify opportunities to transfer load between regions
        """
        opportunities = []
        
        # Find regions with excess capacity and high demand
        for region1, pred1 in predictions_dict.items():
            for region2, pred2 in predictions_dict.items():
                if region1 == region2:
                    continue
                
                # Check if region1 has low demand when region2 has high demand
                avg1 = pred1['predicted_demand'].mean()
                avg2 = pred2['predicted_demand'].mean()
                
                if avg1 < 5000 and avg2 > 8000:
                    opportunities.append({
                        'from_region': region1,
                        'to_region': region2,
                        'potential_transfer': min(5000 - avg1, avg2 - 8000),
                        'benefit': 'Load balancing across regions'
                    })
        
        return opportunities
    
    def optimize_inter_regional_flow(self, predictions_dict):
        """Optimize power flow between regions"""
        optimization = {
            'total_system_load': 0,
            'recommended_transfers': [],
            'cost_savings': 0
        }
        
        # Calculate total system load
        for pred_df in predictions_dict.values():
            optimization['total_system_load'] += pred_df['predicted_demand'].sum()
        
        # Find transfer opportunities
        opportunities = self.identify_load_transfer_opportunities(predictions_dict)
        optimization['recommended_transfers'] = opportunities
        
        # Estimate cost savings (simplified)
        for opp in opportunities:
            optimization['cost_savings'] += opp['potential_transfer'] * 0.05  # $0.05/MW
        
        return optimization

if __name__ == "__main__":
    # Test multi-region forecasting
    from utils.data_generator import EnergyDataGenerator
    
    print("Testing Multi-Region Forecaster...")
    
    forecaster = MultiRegionForecaster()
    
    # Generate data for each region
    historical_data = {}
    for region in forecaster.regions:
        generator = EnergyDataGenerator(days=30)
        historical_data[region] = generator.generate_data()
        forecaster.train_region(region, historical_data[region])
    
    # Predict for all regions
    predictions = forecaster.predict_all_regions(historical_data, hours_ahead=24)
    
    print("\nRegional Predictions:")
    summary = forecaster.get_regional_summary(predictions)
    print(f"Total System Demand: {summary['total_demand']:.2f} MW")
    print(f"System Peak: {summary['peak_demand']:.2f} MW")
    
    print("\nRegion Details:")
    for region, stats in summary['regions'].items():
        print(f"  {region}: Avg={stats['avg_demand']:.2f} MW, Peak={stats['peak_demand']:.2f} MW")
    
    # Check transfer opportunities
    optimization = forecaster.optimize_inter_regional_flow(predictions)
    print(f"\nLoad Transfer Opportunities: {len(optimization['recommended_transfers'])}")
    print(f"Potential Cost Savings: ${optimization['cost_savings']:.2f}")
