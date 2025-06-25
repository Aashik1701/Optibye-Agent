#!/usr/bin/env python3
"""
Notification Service for EMS
Handles alerts, notifications, and messaging
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis.asyncio as redis
from pymongo import MongoClient

from common.base_service import BaseService
from common.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class NotificationChannel:
    """Base class for notification channels"""
    
    async def send(self, notification: Dict[str, Any]) -> bool:
        """Send notification"""
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_host = smtp_config.get('host', 'smtp.gmail.com')
        self.smtp_port = smtp_config.get('port', 587)
        self.smtp_user = smtp_config.get('user')
        self.smtp_password = smtp_config.get('password')
        self.from_email = smtp_config.get('from_email', self.smtp_user)
    
    async def send(self, notification: Dict[str, Any]) -> bool:
        """Send email notification"""
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.warning("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = notification['recipient']
            msg['Subject'] = notification['subject']
            
            body = notification.get('body', notification.get('message', ''))
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, notification['recipient'], text)
            server.quit()
            
            logger.info(f"Email sent to {notification['recipient']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


class WebhookChannel(NotificationChannel):
    """Webhook notification channel"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(self, notification: Dict[str, Any]) -> bool:
        """Send webhook notification"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=notification,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook sent to {self.webhook_url}")
                    return True
                else:
                    logger.error(f"Webhook failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False


class SlackChannel(NotificationChannel):
    """Slack notification channel"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(self, notification: Dict[str, Any]) -> bool:
        """Send Slack notification"""
        try:
            import httpx
            
            # Format for Slack
            slack_message = {
                "text": notification.get('subject', 'EMS Alert'),
                "attachments": [{
                    "color": self._get_color(notification.get('priority', 'medium')),
                    "fields": [
                        {
                            "title": "Message",
                            "value": notification.get('message', ''),
                            "short": False
                        },
                        {
                            "title": "Time",
                            "value": notification.get('timestamp', datetime.now().isoformat()),
                            "short": True
                        },
                        {
                            "title": "Source",
                            "value": notification.get('source', 'EMS Agent'),
                            "short": True
                        }
                    ]
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=slack_message,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info("Slack notification sent")
                    return True
                else:
                    logger.error(f"Slack notification failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _get_color(self, priority: str) -> str:
        """Get color based on priority"""
        colors = {
            'critical': '#ff0000',
            'high': '#ff6600',
            'medium': '#ffcc00',
            'low': '#00cc00',
            'info': '#0066cc'
        }
        return colors.get(priority, '#999999')


class NotificationService(BaseService):
    """Notification service for EMS alerts and messaging"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("notification", config)
        self.mongodb_client = None
        self.redis_client = None
        self.channels = {}
        self.notification_rules = []
        
    async def initialize(self):
        """Initialize the service"""
        await super().initialize()
        
        try:
            # Connect to MongoDB for storing notifications
            mongodb_uri = self.config.get('mongodb_uri')
            mongodb_database = self.config.get('mongodb_database', 'EMS_Database')
            
            self.mongodb_client = MongoClient(mongodb_uri)
            self.db = self.mongodb_client[mongodb_database]
            self.notifications_collection = self.db.notifications
            
            # Connect to Redis for real-time notifications
            redis_host = self.config.get('redis_host', 'localhost')
            redis_port = self.config.get('redis_port', 6379)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )
            
            # Initialize notification channels
            await self._setup_channels()
            
            # Load notification rules
            await self._load_notification_rules()
            
            logger.info("Notification Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Notification Service: {e}")
            raise
    
    async def _setup_channels(self):
        """Setup notification channels"""
        # Email channel
        smtp_config = self.config.get('smtp', {})
        if smtp_config:
            self.channels['email'] = EmailChannel(smtp_config)
        
        # Webhook channels
        webhooks = self.config.get('webhooks', {})
        for name, url in webhooks.items():
            self.channels[f'webhook_{name}'] = WebhookChannel(url)
        
        # Slack channel
        slack_webhook = self.config.get('slack_webhook')
        if slack_webhook:
            self.channels['slack'] = SlackChannel(slack_webhook)
    
    async def _load_notification_rules(self):
        """Load notification rules from config or database"""
        # Default rules
        self.notification_rules = [
            {
                'id': 'anomaly_alert',
                'trigger': 'anomaly_detected',
                'priority': 'high',
                'channels': ['email', 'slack'],
                'template': 'anomaly_detected'
            },
            {
                'id': 'power_threshold',
                'trigger': 'power_threshold_exceeded',
                'priority': 'medium',
                'channels': ['email'],
                'template': 'power_alert'
            },
            {
                'id': 'system_status',
                'trigger': 'system_status_change',
                'priority': 'info',
                'channels': ['slack'],
                'template': 'system_status'
            }
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            health_status = {
                "status": "healthy",
                "service": "notification",
                "timestamp": datetime.now().isoformat(),
                "channels": {}
            }
            
            # Check database connection
            if self.mongodb_client:
                self.mongodb_client.admin.command('ping')
                health_status["database"] = "connected"
            else:
                health_status["database"] = "disconnected"
            
            # Check Redis connection
            if self.redis_client:
                await self.redis_client.ping()
                health_status["redis"] = "connected"
            else:
                health_status["redis"] = "disconnected"
            
            # Check channels
            for channel_name in self.channels:
                health_status["channels"][channel_name] = "configured"
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "notification",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send a notification"""
        try:
            # Validate notification
            if not notification.get('message') and not notification.get('body'):
                raise HTTPException(status_code=400, detail="Message is required")
            
            # Add metadata
            notification_id = f"notif_{datetime.now().timestamp()}"
            notification.update({
                'id': notification_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending',
                'source': notification.get('source', 'EMS Agent')
            })
            
            # Store in database
            self.notifications_collection.insert_one(notification.copy())
            
            # Determine channels to use
            channels_to_use = notification.get('channels', ['email'])
            if isinstance(channels_to_use, str):
                channels_to_use = [channels_to_use]
            
            # Send to each channel
            results = {}
            for channel_name in channels_to_use:
                if channel_name in self.channels:
                    try:
                        success = await self.channels[channel_name].send(notification)
                        results[channel_name] = 'sent' if success else 'failed'
                    except Exception as e:
                        results[channel_name] = f'error: {str(e)}'
                else:
                    results[channel_name] = 'channel_not_configured'
            
            # Update status
            final_status = 'sent' if any(r == 'sent' for r in results.values()) else 'failed'
            
            # Update in database
            self.notifications_collection.update_one(
                {'id': notification_id},
                {'$set': {'status': final_status, 'results': results}}
            )
            
            # Publish to Redis for real-time updates
            if self.redis_client:
                await self.redis_client.publish(
                    'notifications',
                    json.dumps({
                        'id': notification_id,
                        'status': final_status,
                        'notification': notification
                    })
                )
            
            return {
                'success': True,
                'notification_id': notification_id,
                'status': final_status,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_notifications(self, 
                              user_id: Optional[str] = None,
                              status: Optional[str] = None,
                              limit: int = 50) -> Dict[str, Any]:
        """Get notifications"""
        try:
            query = {}
            
            if user_id:
                query['user_id'] = user_id
            
            if status:
                query['status'] = status
            
            notifications = list(
                self.notifications_collection
                .find(query)
                .sort('timestamp', -1)
                .limit(limit)
            )
            
            # Convert ObjectIds to strings
            for notif in notifications:
                notif['_id'] = str(notif['_id'])
            
            return {
                'success': True,
                'notifications': notifications,
                'count': len(notifications)
            }
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def mark_as_read(self, notification_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Mark notification as read"""
        try:
            query = {'id': notification_id}
            if user_id:
                query['user_id'] = user_id
            
            result = self.notifications_collection.update_one(
                query,
                {'$set': {'read': True, 'read_at': datetime.now().isoformat()}}
            )
            
            if result.modified_count > 0:
                return {
                    'success': True,
                    'message': 'Notification marked as read'
                }
            else:
                return {
                    'success': False,
                    'error': 'Notification not found or already read'
                }
                
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_alert_from_anomaly(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert notification from anomaly detection"""
        notification = {
            'type': 'alert',
            'priority': 'high',
            'subject': f"Anomaly Detected - Equipment {anomaly_data.get('equipment_id', 'Unknown')}",
            'message': f"""
Anomaly detected in equipment {anomaly_data.get('equipment_id', 'Unknown')}:

Anomaly Score: {anomaly_data.get('anomaly_score', 'N/A')}
Severity: {anomaly_data.get('severity', 'Unknown')}
Detected At: {anomaly_data.get('detected_at', 'Unknown')}

Features that triggered the anomaly:
{json.dumps(anomaly_data.get('features', {}), indent=2)}

Please check the equipment for any issues.
            """.strip(),
            'channels': ['email', 'slack'],
            'source': 'Anomaly Detection System',
            'metadata': anomaly_data
        }
        
        return await self.send_notification(notification)
    
    async def create_power_threshold_alert(self, equipment_id: str, current_power: float, threshold: float) -> Dict[str, Any]:
        """Create power threshold alert"""
        notification = {
            'type': 'alert',
            'priority': 'medium',
            'subject': f"Power Threshold Exceeded - {equipment_id}",
            'message': f"""
Power consumption threshold exceeded for equipment {equipment_id}:

Current Power: {current_power} kW
Threshold: {threshold} kW
Exceeded by: {current_power - threshold:.2f} kW

Please check the equipment for efficiency issues.
            """.strip(),
            'channels': ['email'],
            'source': 'Power Monitoring System',
            'metadata': {
                'equipment_id': equipment_id,
                'current_power': current_power,
                'threshold': threshold
            }
        }
        
        return await self.send_notification(notification)


# FastAPI app
def create_notification_service():
    """Create and configure the notification service"""
    
    config_manager = ConfigManager()
    config = config_manager.get_service_config('notification')
    
    service = NotificationService(config)
    app = FastAPI(
        title="EMS Notification Service",
        description="Alerts, notifications, and messaging for energy management",
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
    
    @app.post("/send")
    async def send_notification(notification: Dict[str, Any]):
        return await service.send_notification(notification)
    
    @app.get("/notifications")
    async def get_notifications(
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ):
        return await service.get_notifications(user_id, status, limit)
    
    @app.put("/notifications/{notification_id}/read")
    async def mark_as_read(notification_id: str, user_id: Optional[str] = None):
        return await service.mark_as_read(notification_id, user_id)
    
    @app.post("/alerts/anomaly")
    async def create_anomaly_alert(anomaly_data: Dict[str, Any]):
        return await service.create_alert_from_anomaly(anomaly_data)
    
    @app.post("/alerts/power-threshold")
    async def create_power_threshold_alert(request: Dict[str, Any]):
        equipment_id = request.get('equipment_id')
        current_power = request.get('current_power')
        threshold = request.get('threshold')
        
        if not all([equipment_id, current_power, threshold]):
            raise HTTPException(
                status_code=400,
                detail="equipment_id, current_power, and threshold are required"
            )
        
        return await service.create_power_threshold_alert(equipment_id, current_power, threshold)
    
    return app


if __name__ == "__main__":
    app = create_notification_service()
    uvicorn.run(app, host="0.0.0.0", port=8004)
