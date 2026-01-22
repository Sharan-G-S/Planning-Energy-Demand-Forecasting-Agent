"""
Advanced Features API Extension
Adds endpoints for multi-region, EV, battery, and DER features
"""

from flask import Blueprint, jsonify, request
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.multi_region import MultiRegionForecaster
from utils.ev_predictor import EVLoadPredictor
from utils.battery_optimizer import BatteryStorageOptimizer
from utils.der_manager import DERManager
from utils.data_generator import EnergyDataGenerator

# Create blueprint
advanced_bp = Blueprint('advanced', __name__)

# Initialize advanced features
multi_region = MultiRegionForecaster()
ev_predictor = EVLoadPredictor(num_evs=5000)
battery_optimizer = BatteryStorageOptimizer(capacity_mwh=100, power_rating_mw=50)
der_manager = DERManager()

# Initialize with sample data
generator = EnergyDataGenerator(days=30)
sample_data = generator.generate_data()

@advanced_bp.route('/api/advanced/multi-region', methods=['GET'])
def get_multi_region_forecast():
    """Get multi-region energy forecast"""
    try:
        hours = int(request.args.get('hours', 24))
        
        # Generate forecasts for all regions
        historical_data = {}
        predictions = {}
        
        for region in multi_region.regions:
            historical_data[region] = sample_data
            if region not in multi_region.region_models or not multi_region.region_models[region].trained:
                multi_region.train_region(region, sample_data)
            predictions[region] = multi_region.predict_region(region, sample_data, hours)
        
        # Get summary
        summary = multi_region.get_regional_summary(predictions)
        
        # Get optimization
        optimization = multi_region.optimize_inter_regional_flow(predictions)
        
        # Convert predictions to JSON-friendly format
        predictions_json = {}
        for region, pred_df in predictions.items():
            predictions_json[region] = pred_df.to_dict('records')
        
        return jsonify({
            'success': True,
            'regions': multi_region.regions,
            'predictions': predictions_json,
            'summary': summary,
            'optimization': optimization
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@advanced_bp.route('/api/advanced/ev-load', methods=['GET'])
def get_ev_load_prediction():
    """Get electric vehicle load prediction"""
    try:
        hours = int(request.args.get('hours', 24))
        
        # Get EV statistics
        stats = ev_predictor.get_ev_statistics()
        
        # Predict EV load
        forecast = ev_predictor.predict_ev_load(hours)
        
        # Optimize charging
        optimization = ev_predictor.optimize_ev_charging(forecast)
        
        # V2G potential
        v2g = ev_predictor.calculate_v2g_potential()
        
        # Smart charging impact
        impact = ev_predictor.predict_smart_charging_impact(hours)
        
        return jsonify({
            'success': True,
            'fleet_statistics': stats,
            'forecast': forecast.to_dict('records'),
            'optimization': optimization,
            'v2g_potential': v2g,
            'smart_charging_impact': impact
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@advanced_bp.route('/api/advanced/battery', methods=['GET'])
def get_battery_optimization():
    """Get battery storage optimization"""
    try:
        # Get battery status
        status = battery_optimizer.get_battery_status()
        
        # Optimize charging schedule
        schedule = battery_optimizer.optimize_charging_schedule(sample_data)
        
        # Peak shaving benefit
        peak_shaving = battery_optimizer.calculate_peak_shaving_benefit(sample_data)
        
        # Arbitrage potential
        arbitrage = battery_optimizer.calculate_arbitrage_potential(None)
        
        # Frequency regulation
        regulation = battery_optimizer.calculate_frequency_regulation_value()
        
        # Simulation
        simulation = battery_optimizer.simulate_operation(sample_data)
        
        return jsonify({
            'success': True,
            'status': status,
            'schedule': schedule.to_dict('records'),
            'peak_shaving': peak_shaving,
            'arbitrage': arbitrage,
            'frequency_regulation': regulation,
            'simulation': simulation
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@advanced_bp.route('/api/advanced/der', methods=['GET'])
def get_der_management():
    """Get distributed energy resource management"""
    try:
        hours = int(request.args.get('hours', 24))
        
        # Get portfolio summary
        portfolio = der_manager.get_der_portfolio_summary()
        
        # Generate forecasts
        solar_forecast = der_manager.predict_solar_generation(hours)
        wind_forecast = der_manager.predict_wind_generation(hours)
        der_forecast = der_manager.aggregate_der_forecast(hours)
        
        # Optimize dispatch
        dispatch = der_manager.optimize_der_dispatch(sample_data.head(hours), der_forecast)
        
        # Calculate benefits
        benefits = der_manager.calculate_der_benefits(dispatch)
        
        # Expansion opportunities
        opportunities = der_manager.identify_der_expansion_opportunities(dispatch)
        
        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'solar_forecast': solar_forecast.to_dict('records'),
            'wind_forecast': wind_forecast.to_dict('records'),
            'aggregate_forecast': der_forecast.to_dict('records'),
            'dispatch_schedule': dispatch.to_dict('records'),
            'benefits': benefits,
            'expansion_opportunities': opportunities
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@advanced_bp.route('/api/advanced/summary', methods=['GET'])
def get_advanced_features_summary():
    """Get summary of all advanced features"""
    try:
        summary = {
            'multi_region': {
                'enabled': True,
                'regions': len(multi_region.regions),
                'region_names': multi_region.regions
            },
            'ev_load': {
                'enabled': True,
                'num_evs': ev_predictor.num_evs,
                'total_capacity_mwh': round(ev_predictor.num_evs * ev_predictor.avg_battery_capacity / 1000, 2)
            },
            'battery_storage': {
                'enabled': True,
                'capacity_mwh': battery_optimizer.capacity_mwh,
                'power_rating_mw': battery_optimizer.power_rating_mw
            },
            'der_management': {
                'enabled': True,
                'total_renewable_mw': der_manager.resources['solar']['capacity_mw'] + der_manager.resources['wind']['capacity_mw'],
                'resources': list(der_manager.resources.keys())
            }
        }
        
        return jsonify({
            'success': True,
            'features': summary,
            'status': 'All advanced features operational'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Export blueprint
def register_advanced_routes(app):
    """Register advanced feature routes with Flask app"""
    app.register_blueprint(advanced_bp)
    print("✓ Advanced features API registered")
