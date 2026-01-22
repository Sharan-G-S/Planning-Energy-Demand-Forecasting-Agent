"""
Simplified startup script that works without TensorFlow
"""

import sys
import os

# Use lightweight sklearn model (no TensorFlow required)
USE_TENSORFLOW = False
print("Using lightweight sklearn-based model (no TensorFlow required)")

# Patch the import to use lite version
import models.lstm_model_lite as lstm_model_module
sys.modules['models.lstm_model'] = lstm_model_module

# Now import the rest
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from utils.data_generator import EnergyDataGenerator
from utils.grid_optimizer import GridOptimizer
from utils.anomaly_detector import AnomalyDetector
from models.ensemble_predictor_simple import EnsemblePredictor

# Import advanced features API
try:
    from api_advanced import register_advanced_routes
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False
    print("Advanced features not available")

app = Flask(__name__)
CORS(app)

# Register advanced features if available
if ADVANCED_FEATURES:
    register_advanced_routes(app)

historical_data = None
ensemble_model = None
grid_optimizer = GridOptimizer()
anomaly_detector = AnomalyDetector()

def initialize_system():
    global historical_data, ensemble_model
    
    print("\n" + "="*60)
    print("Energy Demand Forecasting Agent")
    print("="*60)
    print("Initializing system...")
    
    data_path = os.path.join(config.DATA_DIR, 'historical_data.csv')
    
    if os.path.exists(data_path):
        print("✓ Loading historical data...")
        historical_data = pd.read_csv(data_path)
        historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'])
    else:
        print("✓ Generating historical data (this may take a minute)...")
        generator = EnergyDataGenerator(days=config.HISTORICAL_DAYS)
        historical_data = generator.save_data(data_path)
    
    print(f"✓ Loaded {len(historical_data)} hours of data")
    
    print("✓ Training forecasting models...")
    ensemble_model = EnsemblePredictor()
    
    try:
        if ensemble_model.load_models():
            print("✓ Loaded pre-trained models")
        else:
            raise FileNotFoundError("No saved models")
    except:
        print("✓ Training new models (first run - may take 2-3 minutes)...")
        ensemble_model.train(historical_data)
        ensemble_model.save_models()
    
    print("✓ System initialization complete!")
    print("="*60 + "\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['GET'])
def predict():
    try:
        hours = int(request.args.get('hours', config.FORECAST_HOURS_DEFAULT))
        hours = min(hours, config.FORECAST_DAYS_MAX * 24)
        
        predictions = ensemble_model.predict_with_confidence(
            historical_data, 
            hours_ahead=hours
        )
        
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
        print(f"Prediction error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/historical', methods=['GET'])
def get_historical():
    try:
        days = int(request.args.get('days', 7))
        hours = days * 24
        
        recent_data = historical_data.tail(hours).copy()
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/optimize', methods=['GET'])
def optimize_grid():
    try:
        hours = int(request.args.get('hours', 24))
        
        predictions = ensemble_model.predict(historical_data, hours_ahead=hours)
        recommendations = grid_optimizer.generate_recommendations(predictions)
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/anomalies', methods=['GET'])
def detect_anomalies():
    try:
        days = int(request.args.get('days', 7))
        hours = days * 24
        
        recent_data = historical_data.tail(hours).copy()
        alerts = anomaly_detector.get_anomaly_alerts(recent_data)
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        current_demand = float(historical_data['energy_demand'].iloc[-1])
        grid_status = grid_optimizer.get_grid_status(current_demand)
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': ensemble_model is not None and ensemble_model.trained,
        'tensorflow_available': USE_TENSORFLOW
    })

if __name__ == '__main__':
    initialize_system()
    
    print(f"\n{'='*60}")
    print("🚀 Energy Demand Forecasting Agent is running!")
    print(f"{'='*60}")
    print(f"📊 Dashboard: http://localhost:{config.PORT}")
    print(f"🔌 API: http://localhost:{config.PORT}/api/health")
    print(f"{'='*60}\n")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
