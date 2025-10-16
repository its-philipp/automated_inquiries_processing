"""
Real Prometheus metrics implementation for the inquiry automation pipeline.
"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from typing import Dict, Any

class RealMetricsCollector:
    """Real Prometheus metrics collector."""
    
    def __init__(self, port=8001):
        """Initialize metrics and start HTTP server."""
        # Counters
        self.inquiries_received = Counter(
            'inquiries_received_total', 
            'Total number of inquiries received', 
            ['source']
        )
        
        self.inquiries_processed = Counter(
            'inquiries_processed_total', 
            'Total number of inquiries processed', 
            ['status']
        )
        
        self.pipeline_errors = Counter(
            'pipeline_errors_total', 
            'Total number of errors in the pipeline', 
            ['stage', 'error_type']
        )
        
        self.routing_decisions = Counter(
            'routing_decisions_total', 
            'Total number of routing decisions made', 
            ['department', 'escalated']
        )
        
        self.model_inferences = Counter(
            'model_inferences_total', 
            'Total number of model inferences', 
            ['model_name', 'prediction_type', 'prediction_value']
        )
        
        # Histograms
        self.processing_duration = Histogram(
            'inquiry_processing_duration_seconds', 
            'Duration of inquiry processing in seconds'
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds', 
            'Duration of HTTP requests in seconds', 
            ['method', 'endpoint', 'status']
        )
        
        # Gauges
        self.system_health = Gauge(
            'system_health_status', 
            'Health status of various system components', 
            ['component']
        )
        
        self.category_distribution = Gauge(
            'category_distribution_total', 
            'Total distribution of predicted categories', 
            ['category']
        )
        
        self.urgency_distribution = Gauge(
            'urgency_distribution_total', 
            'Total distribution of predicted urgency levels', 
            ['urgency']
        )
        
        self.sentiment_distribution = Gauge(
            'sentiment_distribution_total', 
            'Total distribution of predicted sentiments', 
            ['sentiment']
        )
        
        self.active_inquiries = Gauge(
            'active_inquiries_count',
            'Number of active (unprocessed) inquiries'
        )
        
        # Start HTTP server for metrics
        try:
            start_http_server(port)
            print(f"✅ Prometheus metrics server started on port {port}")
        except Exception as e:
            print(f"⚠️  Could not start metrics server: {e}")
    
    def record_inquiry_received(self, source: str):
        """Record an inquiry received."""
        self.inquiries_received.labels(source=source).inc()
    
    def record_inquiry_processed(self, status: str, duration: float):
        """Record an inquiry processed."""
        self.inquiries_processed.labels(status=status).inc()
        self.processing_duration.observe(duration)
    
    def record_pipeline_error(self, stage: str, error_type: str):
        """Record a pipeline error."""
        self.pipeline_errors.labels(stage=stage, error_type=error_type).inc()
    
    def record_routing_decision(self, department: str, priority_score: float, escalated: bool, consultant: str):
        """Record a routing decision."""
        self.routing_decisions.labels(department=department, escalated=str(escalated)).inc()
    
    def record_model_inference(self, model_name: str, prediction_type: str, prediction_value: str, confidence: float, latency: float):
        """Record a model inference."""
        self.model_inferences.labels(
            model_name=model_name, 
            prediction_type=prediction_type, 
            prediction_value=prediction_value
        ).inc()
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record an HTTP request."""
        self.http_request_duration.labels(
            method=method, 
            endpoint=endpoint, 
            status=status
        ).observe(duration)
    
    def set_system_health(self, component: str, is_healthy: bool):
        """Set system health status."""
        self.system_health.labels(component=component).set(1 if is_healthy else 0)
    
    def update_prediction_distributions(self, category: str, urgency: str, sentiment: str):
        """Update prediction distribution counters."""
        self.category_distribution.labels(category=category).inc()
        self.urgency_distribution.labels(urgency=urgency).inc()
        self.sentiment_distribution.labels(sentiment=sentiment).inc()
    
    def set_active_inquiries_count(self, count: int):
        """Set the count of active (unprocessed) inquiries."""
        self.active_inquiries.set(count)

# Global instance
metrics_collector = RealMetricsCollector()

# Decorator for timing functions
def time_function(metric_name: str = "function_duration_seconds"):
    """Decorator to time function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_collector.processing_duration.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_pipeline_error("function_execution", type(e).__name__)
                raise
        return wrapper
    return decorator

# Context manager for timing blocks
class Timer:
    """Context manager for timing code blocks."""
    def __init__(self, metric_collector, operation_name: str):
        self.metric_collector = metric_collector
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metric_collector.processing_duration.observe(duration)
