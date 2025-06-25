#!/usr/bin/env python3
"""
Query Processor Service for EMS
Handles natural language query processing and data retrieval
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
from pymongo import MongoClient

from common.base_service import BaseService
from common.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Natural language query processor"""
    
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.collection = self.db.energy_data
        
        # Query intent patterns
        self.intent_patterns = {
            'power_consumption': [
                r'power\s+consumption', r'energy\s+usage', r'electricity\s+use',
                r'kw\s*h?', r'watts?', r'consumption', r'energy\s+data'
            ],
            'anomalies': [
                r'anomal', r'unusual', r'abnormal', r'irregular', r'outlier',
                r'strange', r'weird', r'problem', r'issue'
            ],
            'trends': [
                r'trend', r'pattern', r'over\s+time', r'historical', r'analysis',
                r'chart', r'graph', r'visualization'
            ],
            'costs': [
                r'cost', r'price', r'bill', r'expense', r'money', r'dollar',
                r'rate', r'tariff'
            ],
            'equipment': [
                r'equipment', r'device', r'meter', r'ikc\d+', r'machine',
                r'asset', r'component'
            ],
            'summary': [
                r'summary', r'overview', r'report', r'status', r'total',
                r'average', r'statistics'
            ]
        }
    
    def classify_intent(self, query: str) -> str:
        """Classify the intent of a query"""
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return 'general'
    
    def extract_equipment_ids(self, query: str) -> List[str]:
        """Extract equipment IDs from query"""
        # Look for IKC patterns
        ikc_pattern = r'ikc\d+'
        matches = re.findall(ikc_pattern, query.lower())
        
        # Also check database for available equipment IDs
        try:
            available_ids = self.collection.distinct('Equipment_ID')
            mentioned_ids = []
            
            for eq_id in available_ids:
                if eq_id.lower() in query.lower():
                    mentioned_ids.append(eq_id)
            
            return list(set(matches + mentioned_ids))
        except:
            return matches
    
    def extract_time_range(self, query: str) -> Dict[str, datetime]:
        """Extract time range from query"""
        now = datetime.now()
        
        if any(word in query.lower() for word in ['today', 'current day']):
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif any(word in query.lower() for word in ['yesterday']):
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif any(word in query.lower() for word in ['week', 'last week']):
            start = now - timedelta(days=7)
            end = now
        elif any(word in query.lower() for word in ['month', 'last month']):
            start = now - timedelta(days=30)
            end = now
        else:
            # Default to last 24 hours
            start = now - timedelta(hours=24)
            end = now
        
        return {'start': start, 'end': end}


class QueryProcessorService(BaseService):
    """Query processor service for EMS natural language queries"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("query_processor", config)
        self.mongodb_client = None
        self.query_processor = None
        
    async def initialize(self):
        """Initialize the service"""
        await super().initialize()
        
        try:
            # Connect to MongoDB
            mongodb_uri = self.config.get('mongodb_uri')
            mongodb_database = self.config.get('mongodb_database', 'EMS_Database')
            
            self.mongodb_client = MongoClient(mongodb_uri)
            db = self.mongodb_client[mongodb_database]
            
            # Initialize query processor
            self.query_processor = QueryProcessor(db)
            
            logger.info("Query Processor Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Query Processor Service: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            if self.mongodb_client:
                # Test database connection
                self.mongodb_client.admin.command('ping')
                db_status = "connected"
            else:
                db_status = "disconnected"
            
            return {
                "status": "healthy",
                "service": "query_processor",
                "database": db_status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "query_processor",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_query(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a natural language query"""
        try:
            if not self.query_processor:
                raise HTTPException(status_code=500, detail="Query processor not initialized")
            
            # Classify intent
            intent = self.query_processor.classify_intent(query)
            
            # Extract entities
            equipment_ids = self.query_processor.extract_equipment_ids(query)
            time_range = self.query_processor.extract_time_range(query)
            
            # Build MongoDB query based on intent
            mongo_query = {}
            
            if equipment_ids:
                mongo_query['Equipment_ID'] = {'$in': equipment_ids}
            
            # Add time filter
            if 'Timestamp' in mongo_query or True:  # Always add time filter
                mongo_query['Timestamp'] = {
                    '$gte': time_range['start'],
                    '$lte': time_range['end']
                }
            
            # Execute query based on intent
            if intent == 'power_consumption':
                result = await self._get_power_consumption(mongo_query)
            elif intent == 'anomalies':
                result = await self._get_anomalies(mongo_query)
            elif intent == 'trends':
                result = await self._get_trends(mongo_query)
            elif intent == 'costs':
                result = await self._get_costs(mongo_query)
            elif intent == 'equipment':
                result = await self._get_equipment_info(mongo_query)
            elif intent == 'summary':
                result = await self._get_summary(mongo_query)
            else:
                result = await self._get_general_info(mongo_query)
            
            return {
                "success": True,
                "query": query,
                "intent": intent,
                "equipment_ids": equipment_ids,
                "time_range": {
                    "start": time_range['start'].isoformat(),
                    "end": time_range['end'].isoformat()
                },
                "result": result,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_power_consumption(self, mongo_query: Dict) -> Dict[str, Any]:
        """Get power consumption data"""
        collection = self.query_processor.collection
        
        # Aggregate power consumption
        pipeline = [
            {"$match": mongo_query},
            {"$group": {
                "_id": "$Equipment_ID",
                "total_power": {"$sum": "$Active_Power_kW"},
                "avg_power": {"$avg": "$Active_Power_kW"},
                "max_power": {"$max": "$Active_Power_kW"},
                "min_power": {"$min": "$Active_Power_kW"},
                "count": {"$sum": 1}
            }}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        return {
            "type": "power_consumption",
            "equipment_data": results,
            "total_equipment": len(results)
        }
    
    async def _get_anomalies(self, mongo_query: Dict) -> Dict[str, Any]:
        """Get anomaly data"""
        # Check for anomalies collection
        try:
            anomalies_collection = self.query_processor.db.anomalies
            anomalies = list(anomalies_collection.find(mongo_query).limit(50))
            
            for anomaly in anomalies:
                anomaly['_id'] = str(anomaly['_id'])
            
            return {
                "type": "anomalies",
                "anomalies": anomalies,
                "count": len(anomalies)
            }
        except:
            return {
                "type": "anomalies",
                "message": "No anomaly data available",
                "count": 0
            }
    
    async def _get_trends(self, mongo_query: Dict) -> Dict[str, Any]:
        """Get trend analysis"""
        collection = self.query_processor.collection
        
        # Get hourly trends
        pipeline = [
            {"$match": mongo_query},
            {"$group": {
                "_id": {
                    "hour": {"$hour": "$Timestamp"},
                    "equipment": "$Equipment_ID"
                },
                "avg_power": {"$avg": "$Active_Power_kW"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.hour": 1}}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        return {
            "type": "trends",
            "hourly_trends": results,
            "data_points": len(results)
        }
    
    async def _get_costs(self, mongo_query: Dict) -> Dict[str, Any]:
        """Calculate energy costs"""
        collection = self.query_processor.collection
        
        # Simple cost calculation (would need actual rate data)
        pipeline = [
            {"$match": mongo_query},
            {"$group": {
                "_id": "$Equipment_ID",
                "total_kwh": {"$sum": "$Active_Power_kW"},
                "count": {"$sum": 1}
            }}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        # Apply estimated rate (would be configurable)
        rate_per_kwh = 0.12  # $0.12 per kWh
        
        for result in results:
            result['estimated_cost'] = result['total_kwh'] * rate_per_kwh
        
        return {
            "type": "costs",
            "cost_analysis": results,
            "rate_per_kwh": rate_per_kwh,
            "currency": "USD"
        }
    
    async def _get_equipment_info(self, mongo_query: Dict) -> Dict[str, Any]:
        """Get equipment information"""
        collection = self.query_processor.collection
        
        # Get equipment summary
        pipeline = [
            {"$match": mongo_query},
            {"$group": {
                "_id": "$Equipment_ID",
                "latest_reading": {"$last": "$$ROOT"},
                "avg_voltage": {"$avg": "$Voltage_V"},
                "avg_current": {"$avg": "$Current_A"},
                "count": {"$sum": 1}
            }}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        return {
            "type": "equipment_info",
            "equipment": results,
            "total_equipment": len(results)
        }
    
    async def _get_summary(self, mongo_query: Dict) -> Dict[str, Any]:
        """Get general summary"""
        collection = self.query_processor.collection
        
        # Overall statistics
        total_records = collection.count_documents(mongo_query)
        
        if total_records > 0:
            # Get aggregated stats
            pipeline = [
                {"$match": mongo_query},
                {"$group": {
                    "_id": None,
                    "total_power": {"$sum": "$Active_Power_kW"},
                    "avg_power": {"$avg": "$Active_Power_kW"},
                    "max_power": {"$max": "$Active_Power_kW"},
                    "avg_voltage": {"$avg": "$Voltage_V"},
                    "avg_current": {"$avg": "$Current_A"},
                    "equipment_count": {"$addToSet": "$Equipment_ID"}
                }}
            ]
            
            result = list(collection.aggregate(pipeline))
            summary = result[0] if result else {}
            summary['total_records'] = total_records
            summary['unique_equipment'] = len(summary.get('equipment_count', []))
            
        else:
            summary = {"message": "No data found for the specified criteria"}
        
        return {
            "type": "summary",
            "summary": summary
        }
    
    async def _get_general_info(self, mongo_query: Dict) -> Dict[str, Any]:
        """Get general information"""
        collection = self.query_processor.collection
        
        # Get recent data
        recent_data = list(collection.find(mongo_query)
                          .sort("Timestamp", -1)
                          .limit(10))
        
        for record in recent_data:
            record['_id'] = str(record['_id'])
            if 'Timestamp' in record:
                record['Timestamp'] = record['Timestamp'].isoformat()
        
        return {
            "type": "general",
            "recent_data": recent_data,
            "count": len(recent_data)
        }


# FastAPI app
def create_query_processor_service():
    """Create and configure the query processor service"""
    
    config_manager = ConfigManager()
    config = config_manager.get_service_config('query_processor')
    
    service = QueryProcessorService(config)
    app = FastAPI(
        title="EMS Query Processor Service",
        description="Natural language query processing for energy data",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup_event():
        await service.initialize()
    
    @app.get("/health")
    async def health_check():
        return await service.health_check()
    
    @app.post("/query")
    async def process_query(request: Dict[str, Any]):
        query = request.get('query', '')
        user_id = request.get('user_id')
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        return await service.process_query(query, user_id)
    
    @app.get("/query/history")
    async def get_query_history(user_id: Optional[str] = None, limit: int = 50):
        # This would typically be stored in a queries collection
        return {
            "message": "Query history feature would be implemented here",
            "user_id": user_id,
            "limit": limit
        }
    
    @app.post("/query/batch")
    async def process_batch_queries(request: Dict[str, Any]):
        queries = request.get('queries', [])
        user_id = request.get('user_id')
        
        if not queries:
            raise HTTPException(status_code=400, detail="Queries list is required")
        
        results = []
        for query in queries:
            result = await service.process_query(query, user_id)
            results.append(result)
        
        return {
            "batch_results": results,
            "total_queries": len(queries),
            "user_id": user_id
        }
    
    return app


if __name__ == "__main__":
    app = create_query_processor_service()
    uvicorn.run(app, host="0.0.0.0", port=8003)
