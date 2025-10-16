"""
Mock sentiment analyzer for demo purposes.
"""
import random
from typing import Tuple, Dict, Any

class SentimentAnalyzer:
    """Mock sentiment analyzer that returns random sentiment."""
    
    def __init__(self):
        self.sentiments = ["positive", "negative", "neutral"]
    
    def predict(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict sentiment for given text."""
        sentiment = random.choice(self.sentiments)
        confidence = random.uniform(0.6, 0.9)
        
        if include_all_scores:
            scores = {sent: random.uniform(0.1, 0.8) for sent in self.sentiments}
            scores[sentiment] = confidence
            return sentiment, confidence, scores
        
        return sentiment, confidence, {}