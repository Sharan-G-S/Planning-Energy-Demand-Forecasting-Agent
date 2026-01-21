"""
Anomaly Detection for Energy Consumption
"""

import numpy as np
import pandas as pd
from scipy import stats
import config

class AnomalyDetector:
    def __init__(self, threshold=config.ANOMALY_THRESHOLD):
        self.threshold = threshold
        self.window = config.ANOMALY_WINDOW
        
    def detect_zscore_anomalies(self, data, window=None):
        """Detect anomalies using Z-score method"""
        if window is None:
            window = self.window
        
        anomalies = []
        data_series = pd.Series(data)
        
        # Calculate rolling mean and std
        rolling_mean = data_series.rolling(window=window, center=True).mean()
        rolling_std = data_series.rolling(window=window, center=True).std()
        
        # Calculate Z-scores
        z_scores = np.abs((data_series - rolling_mean) / rolling_std)
        
        # Identify anomalies
        anomaly_indices = np.where(z_scores > self.threshold)[0]
        
        for idx in anomaly_indices:
            if not np.isnan(z_scores[idx]):
                anomalies.append({
                    'index': int(idx),
                    'value': float(data[idx]),
                    'z_score': float(z_scores[idx]),
                    'expected_range': (
                        float(rolling_mean[idx] - self.threshold * rolling_std[idx]),
                        float(rolling_mean[idx] + self.threshold * rolling_std[idx])
                    ),
                    'severity': 'high' if z_scores[idx] > self.threshold * 1.5 else 'medium'
                })
        
        return anomalies
    
    def detect_iqr_anomalies(self, data):
        """Detect anomalies using Interquartile Range (IQR) method"""
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        anomalies = []
        for idx, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                anomalies.append({
                    'index': int(idx),
                    'value': float(value),
                    'expected_range': (float(lower_bound), float(upper_bound)),
                    'deviation': float(min(abs(value - lower_bound), abs(value - upper_bound))),
                    'severity': 'high' if (value < lower_bound - iqr or value > upper_bound + iqr) else 'medium'
                })
        
        return anomalies
    
    def detect_sudden_changes(self, data, change_threshold=0.3):
        """Detect sudden changes in consumption patterns"""
        changes = []
        data_series = pd.Series(data)
        
        # Calculate percentage change
        pct_change = data_series.pct_change()
        
        # Find significant changes
        significant_changes = np.where(np.abs(pct_change) > change_threshold)[0]
        
        for idx in significant_changes:
            if idx > 0 and not np.isnan(pct_change[idx]):
                changes.append({
                    'index': int(idx),
                    'from_value': float(data[idx-1]),
                    'to_value': float(data[idx]),
                    'change_percent': float(pct_change[idx] * 100),
                    'type': 'spike' if pct_change[idx] > 0 else 'drop',
                    'severity': 'high' if abs(pct_change[idx]) > change_threshold * 2 else 'medium'
                })
        
        return changes
    
    def analyze_anomalies(self, df, target_column='energy_demand'):
        """Comprehensive anomaly analysis"""
        data = df[target_column].values
        
        # Detect using multiple methods
        zscore_anomalies = self.detect_zscore_anomalies(data)
        iqr_anomalies = self.detect_iqr_anomalies(data)
        sudden_changes = self.detect_sudden_changes(data)
        
        # Combine and deduplicate
        all_anomalies = {
            'zscore_anomalies': zscore_anomalies,
            'iqr_anomalies': iqr_anomalies,
            'sudden_changes': sudden_changes,
            'total_anomalies': len(zscore_anomalies) + len(iqr_anomalies) + len(sudden_changes),
            'anomaly_rate': round((len(zscore_anomalies) / len(data)) * 100, 2)
        }
        
        return all_anomalies
    
    def get_anomaly_alerts(self, df, target_column='energy_demand'):
        """Generate user-friendly anomaly alerts"""
        anomalies = self.analyze_anomalies(df, target_column)
        alerts = []
        
        # Z-score anomalies
        for anom in anomalies['zscore_anomalies'][:5]:  # Top 5
            timestamp = df.iloc[anom['index']]['timestamp'] if 'timestamp' in df.columns else f"Index {anom['index']}"
            alerts.append({
                'type': 'statistical_anomaly',
                'severity': anom['severity'],
                'timestamp': str(timestamp),
                'message': f"Unusual consumption detected: {anom['value']:.0f} MW (Z-score: {anom['z_score']:.2f})",
                'recommendation': 'Investigate potential equipment malfunction or unexpected load'
            })
        
        # Sudden changes
        for change in anomalies['sudden_changes'][:3]:  # Top 3
            timestamp = df.iloc[change['index']]['timestamp'] if 'timestamp' in df.columns else f"Index {change['index']}"
            alerts.append({
                'type': 'sudden_change',
                'severity': change['severity'],
                'timestamp': str(timestamp),
                'message': f"Sudden {change['type']}: {abs(change['change_percent']):.1f}% change ({change['from_value']:.0f} → {change['to_value']:.0f} MW)",
                'recommendation': 'Check for grid events, equipment failures, or data quality issues'
            })
        
        return alerts
    
    def calculate_anomaly_score(self, value, historical_data):
        """Calculate anomaly score for a single value"""
        mean = np.mean(historical_data)
        std = np.std(historical_data)
        
        if std == 0:
            return 0
        
        z_score = abs((value - mean) / std)
        
        # Normalize to 0-100 scale
        anomaly_score = min(100, (z_score / self.threshold) * 100)
        
        return round(anomaly_score, 2)

if __name__ == "__main__":
    # Test anomaly detector
    from data_generator import EnergyDataGenerator
    
    generator = EnergyDataGenerator(days=30)
    df = generator.generate_data()
    
    detector = AnomalyDetector()
    alerts = detector.get_anomaly_alerts(df)
    
    print("Anomaly Alerts:")
    for alert in alerts:
        print(f"\n[{alert['severity'].upper()}] {alert['type']}")
        print(f"  Time: {alert['timestamp']}")
        print(f"  {alert['message']}")
        print(f"  Recommendation: {alert['recommendation']}")
