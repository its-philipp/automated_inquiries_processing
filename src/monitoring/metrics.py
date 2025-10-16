"""
Mock metrics collector for demo purposes.
"""
import time
from typing import Dict, Any

class MetricsCollector:
    """Mock metrics collector for monitoring."""
    
    @staticmethod
    def record_http_request(method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        pass
    
    @staticmethod
    def record_inquiry_received(source: str):
        """Record inquiry received metrics."""
        pass
    
    @staticmethod
    def record_model_inference(model_name: str, task: str, prediction: str, confidence: float, duration: float):
        """Record model inference metrics."""
        pass
    
    @staticmethod
    def record_prediction_distributions(category: str, urgency: str, sentiment: str):
        """Record prediction distribution metrics."""
        pass
    
    @staticmethod
    def record_routing_decision(department: str, priority_score: float, escalated: bool, consultant: str):
        """Record routing decision metrics."""
        pass
    
    @staticmethod
    def record_inquiry_processed(status: str, duration: float):
        """Record inquiry processing metrics."""
        pass
    
    @staticmethod
    def record_pipeline_error(component: str, error_type: str):
        """Record pipeline error metrics."""
        pass
    
    @staticmethod
    def set_system_health(component: str, healthy: bool):
        """Set system health status."""
        pass