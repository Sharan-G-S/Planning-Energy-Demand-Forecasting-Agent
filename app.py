"""
Energy Demand Forecasting Agent - Flask API
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from utils.data_generator import EnergyDataGenerator
from utils.grid_optimizer import GridOptimizer
from utils.anomaly_detector import AnomalyDetector
from models.ensemble_predictor import EnsemblePredictor

app = Flask(__name__)
CORS(app)

# Global variables
historical_data = None
ensemble_model = None
grid_optimizer = GridOptimizer()
anomaly_detector = AnomalyDetector()

def initialize_system():
    """Initialize the forecasting system"""
    global historical_data, ensemble_model
    
    print("Initializing Energy Demand Forecasting Agent...")
    
    # Generate or load historical data
    data_path = os.path.join(config.DATA_DIR, 'historical_data.csv')
    
    if os.path.exists(data_path):
        print("Loading historical data...")
        historical_data = pd.read_csv(data_path)
        historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'])
    else:
        print("Generating historical data...")
        generator = EnergyDataGenerator(days=config.HISTORICAL_DAYS)
        historical_data = generator.save_data(data_path)
    
    print(f"Loaded {len(historical_data)} hours of historical data")
    
    # Train ensemble model
    print("Training forecasting models...")
    ensemble_model = EnsemblePredictor()
    
    try:
        # Try to load existing models
        if ensemble_model.load_models():
            print("Loaded pre-trained models")
        else:
            raise FileNotFoundError("No saved models found")
    except:
        # Train new models
        print("Training new models (this may take a few minutes)...")
        ensemble_model.train(historical_data)
        ensemble_model.save_models()
    
    print("System initialization complete!")

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/predict', methods=['GET'])
def predict():
    """Generate energy demand forecast"""
    try:
        hours = int(request.args.get('hours', config.FORECAST_HOURS_DEFAULT))
        hours = min(hours, config.FORECAST_DAYS_MAX * 24)  # Cap at max
        
        # Generate predictions
        predictions = ensemble_model.predict_with_confidence(
            historical_data, 
            hours_ahead=hours
        )
        
        # Convert to JSON-friendly format
        result = {
            'success': True,
            'forecast_hours': hours,
            'predictions': predictions.to_dict('records'),
            'summary': {
                'avg_demand': float(predictions['predicted_demand'].mean()),
                'max_demand': float(predictions['predicted_demand'].max()),
                'min_demand': float(predictions['predicted_demand'].min()),
                'avg_confidence': float(predictions['confidence'].mean())
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/historical', methods=['GET'])
def get_historical():
    """Get historical energy consumption data"""
    try:
        days = int(request.args.get('days', 7))
        hours = days * 24
        
        # Get recent data
        recent_data = historical_data.tail(hours).copy()
        
        # Convert to JSON
        result = {
            'success': True,
            'data': recent_data.to_dict('records'),
            'summary': {
                'avg_demand': float(recent_data['energy_demand'].mean()),
                'max_demand': float(recent_data['energy_demand'].max()),
                'min_demand': float(recent_data['energy_demand'].min()),
                'total_hours': len(recent_data)
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/optimize', methods=['GET'])
def optimize_grid():
    """Get grid optimization recommendations"""
    try:
        hours = int(request.args.get('hours', 24))
        
        # Get forecast
        predictions = ensemble_model.predict(historical_data, hours_ahead=hours)
        
        # Generate recommendations
        recommendations = grid_optimizer.generate_recommendations(predictions)
        
        # Calculate cost optimization
        cost_analysis = grid_optimizer.calculate_cost_optimization(predictions)
        
        result = {
            'success': True,
            'recommendations': recommendations,
            'cost_analysis': cost_analysis,
            'load_analysis': {
                'peak_load': float(predictions['predicted_demand'].max()),
                'avg_load': float(predictions['predicted_demand'].mean()),
                'load_factor': float(predictions['predicted_demand'].mean() / config.MAX_GRID_CAPACITY)
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anomalies', methods=['GET'])
def detect_anomalies():
    """Detect anomalies in energy consumption"""
    try:
        days = int(request.args.get('days', 7))
        hours = days * 24
        
        # Get recent data
        recent_data = historical_data.tail(hours).copy()
        
        # Detect anomalies
        alerts = anomaly_detector.get_anomaly_alerts(recent_data)
        
        # Get anomaly analysis
        analysis = anomaly_detector.analyze_anomalies(recent_data)
        
        result = {
            'success': True,
            'alerts': alerts,
            'analysis': {
                'total_anomalies': analysis['total_anomalies'],
                'anomaly_rate': analysis['anomaly_rate'],
                'zscore_count': len(analysis['zscore_anomalies']),
                'sudden_changes': len(analysis['sudden_changes'])
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics and current status"""
    try:
        # Current demand (last data point)
        current_demand = float(historical_data['energy_demand'].iloc[-1])
        
        # Grid status
        grid_status = grid_optimizer.get_grid_status(current_demand)
        
        # Recent statistics
        recent_24h = historical_data.tail(24)
        
        result = {
            'success': True,
            'current': {
                'demand': current_demand,
                'timestamp': historical_data['timestamp'].iloc[-1].isoformat(),
                'temperature': float(historical_data['temperature'].iloc[-1])
            },
            'grid_status': grid_status,
            'last_24h': {
                'avg_demand': float(recent_24h['energy_demand'].mean()),
                'max_demand': float(recent_24h['energy_demand'].max()),
                'min_demand': float(recent_24h['energy_demand'].min()),
                'variance': float(recent_24h['energy_demand'].std())
            },
            'system': {
                'total_data_points': len(historical_data),
                'data_start': historical_data['timestamp'].iloc[0].isoformat(),
                'data_end': historical_data['timestamp'].iloc[-1].isoformat(),
                'model_trained': ensemble_model.trained
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': ensemble_model is not None and ensemble_model.trained
    })

if __name__ == '__main__':
    # Initialize system
    initialize_system()
    
    # Run Flask app
    print(f"\n{'='*60}")
    print("Energy Demand Forecasting Agent is running!")
    print(f"Dashboard: http://localhost:{config.PORT}")
    print(f"{'='*60}\n")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
