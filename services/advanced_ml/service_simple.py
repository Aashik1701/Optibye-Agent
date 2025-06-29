#!/usr/bin/env python3
"""
Simplified Advanced ML Service - No XGBoost
Provides basic ML functionality without XGBoost dependency
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedAdvancedMLService:
    """Simplified Advanced ML Service without XGBoost"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.app = FastAPI(title="EMS Advanced ML Service", version="1.0.0")
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "service": "advanced_ml",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "models_loaded": len(self.models),
                "available_algorithms": ["isolation_forest", "statistical_analysis"]
            }
        
        @self.app.post("/predict/anomaly")
        async def predict_anomaly(data: Dict[str, Any]):
            """Detect anomalies in energy data"""
            try:
                energy_data = data.get("energy_data", [])
                if not energy_data:
                    raise HTTPException(status_code=400, detail="No energy data provided")
                
                # Use Isolation Forest for anomaly detection
                anomalies = await self.detect_anomalies_isolation_forest(energy_data)
                
                return {
                    "success": True,
                    "anomalies": anomalies,
                    "algorithm": "isolation_forest",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in anomaly prediction: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/predict/consumption")
        async def predict_consumption(data: Dict[str, Any]):
            """Predict energy consumption using simple forecasting"""
            try:
                historical_data = data.get("historical_data", [])
                forecast_horizon = data.get("horizon", 24)  # hours
                
                if not historical_data:
                    raise HTTPException(status_code=400, detail="No historical data provided")
                
                # Simple linear trend forecasting
                predictions = await self.predict_consumption_simple(historical_data, forecast_horizon)
                
                return {
                    "success": True,
                    "predictions": predictions,
                    "algorithm": "linear_trend",
                    "horizon_hours": forecast_horizon,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in consumption prediction: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/optimize/energy")
        async def optimize_energy(data: Dict[str, Any]):
            """Provide energy optimization recommendations"""
            try:
                current_usage = data.get("current_usage", {})
                target_reduction = data.get("target_reduction_percent", 10)
                
                recommendations = await self.generate_optimization_recommendations(
                    current_usage, target_reduction
                )
                
                return {
                    "success": True,
                    "recommendations": recommendations,
                    "target_reduction_percent": target_reduction,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in energy optimization: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def detect_anomalies_isolation_forest(self, energy_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies using Isolation Forest"""
        try:
            # Extract numerical features
            features = []
            timestamps = []
            
            for point in energy_data:
                if isinstance(point, dict):
                    feature_vector = [
                        point.get('energy_consumption', 0),
                        point.get('voltage', 0),
                        point.get('current', 0),
                        point.get('power_factor', 0)
                    ]
                    features.append(feature_vector)
                    timestamps.append(point.get('timestamp', datetime.now().isoformat()))
            
            if len(features) < 10:
                return [{"message": "Insufficient data for anomaly detection (minimum 10 points required)"}]
            
            # Convert to numpy array
            X = np.array(features)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(X_scaled)
            
            # Extract anomalies
            anomalies = []
            for i, label in enumerate(anomaly_labels):
                if label == -1:  # Anomaly
                    anomaly_score = iso_forest.score_samples([X_scaled[i]])[0]
                    anomalies.append({
                        "timestamp": timestamps[i],
                        "data_point": energy_data[i],
                        "anomaly_score": float(anomaly_score),
                        "severity": "high" if anomaly_score < -0.5 else "medium"
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in isolation forest anomaly detection: {e}")
            return [{"error": str(e)}]
    
    async def predict_consumption_simple(self, historical_data: List[Dict[str, Any]], horizon: int) -> List[Dict[str, Any]]:
        """Simple linear trend forecasting"""
        try:
            # Extract consumption values and timestamps
            consumptions = []
            timestamps = []
            
            for point in historical_data:
                if isinstance(point, dict):
                    consumptions.append(point.get('energy_consumption', 0))
                    timestamps.append(point.get('timestamp', datetime.now().isoformat()))
            
            if len(consumptions) < 5:
                return [{"message": "Insufficient historical data for prediction (minimum 5 points required)"}]
            
            # Simple linear regression trend
            x = np.arange(len(consumptions))
            y = np.array(consumptions)
            
            # Calculate trend
            z = np.polyfit(x, y, 1)
            trend_slope = z[0]
            trend_intercept = z[1]
            
            # Generate predictions
            predictions = []
            last_timestamp = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
            
            for i in range(1, horizon + 1):
                future_timestamp = last_timestamp + timedelta(hours=i)
                predicted_value = trend_slope * (len(consumptions) + i) + trend_intercept
                
                # Add some uncertainty bounds
                uncertainty = abs(predicted_value * 0.1)  # 10% uncertainty
                
                predictions.append({
                    "timestamp": future_timestamp.isoformat(),
                    "predicted_consumption": max(0, float(predicted_value)),
                    "confidence_lower": max(0, float(predicted_value - uncertainty)),
                    "confidence_upper": max(0, float(predicted_value + uncertainty)),
                    "trend_slope": float(trend_slope)
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in consumption prediction: {e}")
            return [{"error": str(e)}]
    
    async def generate_optimization_recommendations(self, current_usage: Dict[str, Any], target_reduction: float) -> List[Dict[str, Any]]:
        """Generate energy optimization recommendations"""
        try:
            current_consumption = current_usage.get('energy_consumption', 0)
            current_power_factor = current_usage.get('power_factor', 1.0)
            current_voltage = current_usage.get('voltage', 230)
            
            recommendations = []
            
            # Power factor improvement
            if current_power_factor < 0.9:
                potential_savings = current_consumption * (0.9 - current_power_factor) * 0.1
                recommendations.append({
                    "category": "Power Factor Improvement",
                    "description": "Install power factor correction capacitors",
                    "potential_savings_kwh": potential_savings,
                    "estimated_cost": "Medium",
                    "priority": "High",
                    "implementation_time": "2-4 weeks"
                })
            
            # Voltage optimization
            if current_voltage > 240:
                voltage_savings = current_consumption * 0.02  # 2% per 10V reduction
                recommendations.append({
                    "category": "Voltage Optimization",
                    "description": "Optimize voltage levels to reduce consumption",
                    "potential_savings_kwh": voltage_savings,
                    "estimated_cost": "Low",
                    "priority": "Medium",
                    "implementation_time": "1-2 weeks"
                })
            
            # Load balancing
            recommendations.append({
                "category": "Load Balancing",
                "description": "Implement load scheduling to reduce peak demand",
                "potential_savings_kwh": current_consumption * 0.05,  # 5% savings
                "estimated_cost": "Low",
                "priority": "Medium",
                "implementation_time": "1-3 days"
            })
            
            # Energy monitoring
            recommendations.append({
                "category": "Enhanced Monitoring",
                "description": "Install sub-metering for detailed energy tracking",
                "potential_savings_kwh": current_consumption * 0.03,  # 3% savings
                "estimated_cost": "Medium",
                "priority": "Low",
                "implementation_time": "1-2 weeks"
            })
            
            # Calculate total potential savings
            total_savings = sum(rec.get('potential_savings_kwh', 0) for rec in recommendations)
            
            recommendations.append({
                "category": "Summary",
                "description": f"Total potential energy reduction: {total_savings:.2f} kWh",
                "potential_savings_kwh": total_savings,
                "target_achieved": total_savings >= (current_consumption * target_reduction / 100),
                "target_reduction_kwh": current_consumption * target_reduction / 100
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return [{"error": str(e)}]

def create_advanced_ml_service(config: Dict[str, Any] = None) -> SimplifiedAdvancedMLService:
    """Factory function to create advanced ML service"""
    if config is None:
        config = {
            "service_name": "advanced_ml",
            "port": int(os.getenv("SERVICE_PORT", 8003)),
            "host": "0.0.0.0"
        }
    
    return SimplifiedAdvancedMLService(config)

if __name__ == "__main__":
    service = create_advanced_ml_service()
    
    logger.info("Starting Advanced ML Service (Simplified)...")
    logger.info("Available algorithms: Isolation Forest, Linear Trend, Statistical Analysis")
    
    uvicorn.run(
        service.app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
