"""
RoBERTa-based sentiment analyzer using Hugging Face transformers.
"""
import torch
from transformers import pipeline
from typing import Tuple, Dict, Any
import logging
import os
from .model_cache import get_cached_sentiment_analyzer

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """RoBERTa-based sentiment analyzer."""
    
    def __init__(self):
        self.sentiments = ["positive", "negative", "neutral"]
        
        # Initialize the sentiment analysis pipeline using cache
        try:
            # Check if running on macOS host - force keyword-based fallback for memory optimization
            is_macos = (
                os.environ.get('HOST_OS') == 'Darwin' or 
                'mac' in os.environ.get('HOSTNAME', '').lower() or
                os.environ.get('MACOS_OPTIMIZATION', '').lower() == 'true'
            )
            
            if is_macos:
                logger.warning("🔄 macOS host detected - using keyword-based sentiment analyzer for memory optimization")
                self.analyzer = None
                logger.info("✅ Keyword-based sentiment analyzer initialized successfully")
                return
            
            self.analyzer = get_cached_sentiment_analyzer()
            if self.analyzer is None:
                logger.warning("🔄 Failed to get cached sentiment analyzer, initializing new one")
                self.analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment",  # Smaller model (500MB vs 1GB+)
                    device=0 if torch.cuda.is_available() else -1,
                    max_length=512,  # Limit input length to reduce memory usage
                    batch_size=1  # Process one at a time to reduce memory usage
                )
            logger.info("✅ RoBERTa sentiment analyzer initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RoBERTa sentiment analyzer: {e}")
            logger.warning("🔄 Falling back to keyword-based sentiment analyzer for macOS compatibility")
            # Fallback to keyword-based analyzer
            self.analyzer = None
            logger.warning("🔄 Falling back to mock sentiment analyzer")
    
    def predict(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict sentiment using RoBERTa or fallback to mock."""
        if not text:
            return "neutral", 0.5, {}
        
        # Use RoBERTa analyzer if available
        if self.analyzer is not None:
            try:
                return self._predict_with_roberta(text, include_all_scores)
            except Exception as e:
                logger.error(f"❌ RoBERTa sentiment prediction failed: {e}")
                logger.warning("🔄 Falling back to mock sentiment prediction")
                return self._predict_mock(text, include_all_scores)
        else:
            return self._predict_mock(text, include_all_scores)
    
    def _predict_with_roberta(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict sentiment using RoBERTa."""
        # Run sentiment analysis
        result = self.analyzer(text)
        
        # Map RoBERTa labels to our sentiment labels
        label_mapping = {
            "LABEL_0": "negative",  # Negative
            "LABEL_1": "neutral",   # Neutral  
            "LABEL_2": "positive"   # Positive
        }
        
        sentiment = label_mapping.get(result[0]['label'], "neutral")
        confidence = result[0]['score']
        
        if include_all_scores:
            # For RoBERTa, we only get the top prediction, so we'll estimate others
            all_scores = {}
            for sent in self.sentiments:
                if sent == sentiment:
                    all_scores[sent] = confidence
                else:
                    # Distribute remaining probability among other sentiments
                    all_scores[sent] = (1.0 - confidence) / (len(self.sentiments) - 1)
            return sentiment, confidence, all_scores
        
        return sentiment, confidence, {}
    
    def _predict_mock(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Fallback mock sentiment prediction."""
        import random
        
        # Simple heuristic-based sentiment detection
        text_lower = text.lower()
        
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "love", "happy", "satisfied", "thank", "perfect"]
        negative_words = ["bad", "terrible", "awful", "horrible", "hate", "angry", "frustrated", "disappointed", "problem", "issue", "error"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.9, 0.6 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.9, 0.6 + (negative_count * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.7
        
        if include_all_scores:
            all_scores = {}
            for sent in self.sentiments:
                if sent == sentiment:
                    all_scores[sent] = confidence
                else:
                    all_scores[sent] = (1.0 - confidence) / (len(self.sentiments) - 1)
            return sentiment, confidence, all_scores
        
        return sentiment, confidence, {}