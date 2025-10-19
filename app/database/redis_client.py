import redis
import json
from typing import Optional, Callable
import asyncio
from app.config import get_settings

settings = get_settings()

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
        self.pubsub = self.client.pubsub()
    
    def publish(self, channel: str, message: dict):
        """Publish message to a channel"""
        self.client.publish(channel, json.dumps(message))
    
    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel"""
        self.pubsub.subscribe(**{channel: callback})
        thread = self.pubsub.run_in_thread(sleep_time=0.01)
        return thread
    
    def set_session_data(self, session_id: str, data: dict, expiry: int = 3600):
        """Store session data with expiry"""
        self.client.setex(
            f"session:{session_id}",
            expiry,
            json.dumps(data)
        )
    
    def get_session_data(self, session_id: str) -> Optional[dict]:
        """Retrieve session data"""
        data = self.client.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    def delete_session_data(self, session_id: str):
        """Delete session data"""
        self.client.delete(f"session:{session_id}")
