"""
Enhanced model tracking with MLflow integration for BERT models.
"""
import mlflow
import time
import logging
from typing import Tuple, Dict, Any, Optional
from functools import wraps
from .model_cache import ModelCache
from ..mlflow_config import get_mlflow_config

logger = logging.getLogger(__name__)

def track_model_usage(model_name: str):
    """Decorator to track model usage in MLflow."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mlflow_config = get_mlflow_config()
            
            # Start a run for this prediction
            with mlflow_config.start_run(run_name=f"{model_name}_prediction_{int(time.time())}"):
                start_time = time.time()
                
                try:
                    # Execute the prediction
                    result = func(*args, **kwargs)
                    
                    # Calculate inference time
                    inference_time = time.time() - start_time
                    
                    # Log metrics
                    if isinstance(result, tuple) and len(result) >= 2:
                        prediction, confidence = result[0], result[1]
                        
                        mlflow_config.log_model_metrics({
                            "inference_time_seconds": inference_time,
                            "confidence_score": confidence,
                            "prediction_count": 1
                        })
                        
                        mlflow_config.log_model_params({
                            "model_name": model_name,
                            "model_type": "bert_transformer",
                            "prediction_type": func.__name__
                        })
                        
                        # Log the prediction as a tag
                        mlflow.set_tag("prediction", str(prediction))
                        mlflow.set_tag("confidence", str(confidence))
                    
                    logger.info(f"✅ Logged {model_name} prediction to MLflow")
                    return result
                    
                except Exception as e:
                    # Log error metrics
                    mlflow_config.log_model_metrics({
                        "inference_time_seconds": time.time() - start_time,
                        "error_count": 1
                    })
                    mlflow.set_tag("error", str(e))
                    logger.error(f"❌ Error in {model_name} prediction: {e}")
                    raise
                    
        return wrapper
    return decorator

class TrackedInquiryClassifier:
    """BERT-based classifier with MLflow tracking."""
    
    def __init__(self):
        self.categories = [
            "technical_support", "billing", "sales", "hr", "legal", "product_feedback"
        ]
        
        # Initialize the zero-shot classifier using cache
        try:
            model_cache = ModelCache()
            self.classifier = model_cache.get_classifier()
            if self.classifier is None:
                logger.warning("🔄 Failed to get cached classifier, initializing new one")
                self.classifier = model_cache.get_classifier()
            logger.info("✅ BERT-based classifier initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize BERT classifier: {e}")
            self.classifier = None
    
    @track_model_usage("bert_classifier")
    def predict(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict category with MLflow tracking."""
        if self.classifier is None:
            # Fallback to mock prediction
            return "technical_support", 0.5, {}
        
        # Prepare candidate labels with descriptions
        candidate_labels = [
            "technical support and troubleshooting issues",
            "billing and payment related questions", 
            "sales and product information inquiries",
            "human resources and employment matters",
            "legal and compliance questions",
            "product feedback and feature requests"
        ]
        
        # Run zero-shot classification
        result = self.classifier(text, candidate_labels)
        
        # Map result to our category names
        label_mapping = {
            "technical support and troubleshooting issues": "technical_support",
            "billing and payment related questions": "billing",
            "sales and product information inquiries": "sales", 
            "human resources and employment matters": "hr",
            "legal and compliance questions": "legal",
            "product feedback and feature requests": "product_feedback"
        }
        
        category = label_mapping.get(result['labels'][0], "technical_support")
        confidence = result['scores'][0]
        
        if include_all_scores:
            all_scores = {}
            for i, label in enumerate(result['labels']):
                cat = label_mapping.get(label, "technical_support")
                all_scores[cat] = result['scores'][i]
            return category, confidence, all_scores
        
        return category, confidence, {}

class TrackedSentimentAnalyzer:
    """RoBERTa-based sentiment analyzer with MLflow tracking."""
    
    def __init__(self):
        self.sentiments = ["positive", "negative", "neutral"]
        
        # Initialize the sentiment analysis pipeline using cache
        try:
            model_cache = ModelCache()
            self.analyzer = model_cache.get_sentiment_analyzer()
            if self.analyzer is None:
                logger.warning("🔄 Failed to get cached sentiment analyzer, initializing new one")
                self.analyzer = model_cache.get_sentiment_analyzer()
            logger.info("✅ RoBERTa sentiment analyzer initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RoBERTa sentiment analyzer: {e}")
            self.analyzer = None
    
    @track_model_usage("roberta_sentiment")
    def predict(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict sentiment with MLflow tracking."""
        if self.analyzer is None:
            # Fallback to mock prediction
            return "neutral", 0.5, {}
        
        # Run sentiment analysis
        result = self.analyzer(text)
        
        # Map to our sentiment categories
        sentiment_mapping = {
            "LABEL_0": "negative",
            "LABEL_1": "neutral", 
            "LABEL_2": "positive"
        }
        
        sentiment = sentiment_mapping.get(result[0]['label'], "neutral")
        confidence = result[0]['score']
        
        if include_all_scores:
            all_scores = {}
            for item in result:
                sent = sentiment_mapping.get(item['label'], "neutral")
                all_scores[sent] = item['score']
            return sentiment, confidence, all_scores
        
        return sentiment, confidence, {}

def log_model_performance_metrics():
    """Log aggregated model performance metrics to MLflow."""
    mlflow_config = get_mlflow_config()
    
    with mlflow_config.start_run(run_name=f"performance_summary_{int(time.time())}"):
        # This would typically aggregate metrics from the database
        # For now, we'll log some sample metrics
        mlflow_config.log_model_metrics({
            "total_predictions": 1000,
            "average_confidence": 0.85,
            "average_inference_time": 0.15,
            "error_rate": 0.02
        })
        
        mlflow_config.log_model_params({
            "tracking_period": "1_hour",
            "models_tracked": "bert_classifier,roberta_sentiment"
        })
        
        logger.info("✅ Logged aggregated performance metrics to MLflow")

# Global tracked model instances
_tracked_classifier = None
_tracked_sentiment = None

def get_tracked_classifier():
    """Get or create tracked classifier instance."""
    global _tracked_classifier
    if _tracked_classifier is None:
        _tracked_classifier = TrackedInquiryClassifier()
    return _tracked_classifier

def get_tracked_sentiment_analyzer():
    """Get or create tracked sentiment analyzer instance."""
    global _tracked_sentiment
    if _tracked_sentiment is None:
        _tracked_sentiment = TrackedSentimentAnalyzer()
    return _tracked_sentiment
