"""
Model caching and management utilities for BERT models.
"""
import os
import logging
from typing import Dict, Any, Optional
from functools import lru_cache
import torch
from transformers import pipeline

logger = logging.getLogger(__name__)

class ModelCache:
    """Singleton class for caching and managing BERT models."""
    
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._setup_cache_directories()
    
    def _setup_cache_directories(self):
        """Set up cache directories for transformers and huggingface."""
        # Use home directory for local development, /app for Docker
        if os.path.exists('/app'):
            cache_dir = os.getenv('TRANSFORMERS_CACHE', '/app/.cache/transformers')
            hf_home = os.getenv('HF_HOME', '/app/.cache/huggingface')
        else:
            # Local development - use home directory
            home_dir = os.path.expanduser('~')
            cache_dir = os.getenv('TRANSFORMERS_CACHE', os.path.join(home_dir, '.cache', 'transformers'))
            hf_home = os.getenv('HF_HOME', os.path.join(home_dir, '.cache', 'huggingface'))
        
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(hf_home, exist_ok=True)
        
        logger.info(f"✅ Cache directories set up: {cache_dir}, {hf_home}")
    
    def get_classifier(self) -> Optional[pipeline]:
        """Get or create the zero-shot classifier."""
        if 'classifier' not in self._models:
            try:
                print("🔄 Loading BERT zero-shot classifier...")
                print("📥 This may take a moment as we download the model...")
                self._models['classifier'] = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
                print("✅ BERT classifier loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load BERT classifier: {e}")
                return None
        
        return self._models['classifier']
    
    def get_sentiment_analyzer(self) -> Optional[pipeline]:
        """Get or create the sentiment analyzer."""
        if 'sentiment' not in self._models:
            try:
                print("🔄 Loading RoBERTa sentiment analyzer...")
                print("📥 This may take a moment as we download the model...")
                self._models['sentiment'] = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=0 if torch.cuda.is_available() else -1
                )
                print("✅ RoBERTa sentiment analyzer loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load RoBERTa sentiment analyzer: {e}")
                return None
        
    def get_urgency_detector(self) -> Optional[pipeline]:
        """Get or create the urgency detector."""
        if 'urgency' not in self._models:
            try:
                logger.info("🔄 Loading BERT urgency detector...")
                self._models['urgency'] = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("✅ BERT urgency detector loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load BERT urgency detector: {e}")
                return None
        
        return self._models['urgency']
    
    def clear_cache(self):
        """Clear all cached models."""
        logger.info("🔄 Clearing model cache...")
        for model_name in list(self._models.keys()):
            del self._models[model_name]
        logger.info("✅ Model cache cleared")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        info = {
            'loaded_models': list(self._models.keys()),
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'cache_directory': os.getenv('TRANSFORMERS_CACHE', '/app/.cache/transformers'),
            'total_memory_usage': self._get_memory_usage()
        }
        return info
    
    def _get_memory_usage(self) -> str:
        """Get current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return f"{memory_mb:.1f} MB"
        except ImportError:
            return "Unknown (psutil not available)"

# Global model cache instance
model_cache = ModelCache()

@lru_cache(maxsize=1)
def get_cached_classifier():
    """Get cached classifier with LRU caching."""
    return model_cache.get_classifier()

@lru_cache(maxsize=1)
def get_cached_sentiment_analyzer():
    """Get cached sentiment analyzer with LRU caching."""
    return model_cache.get_sentiment_analyzer()

@lru_cache(maxsize=1)
def get_cached_urgency_detector():
    """Get cached urgency detector with LRU caching."""
    return model_cache.get_urgency_detector()
