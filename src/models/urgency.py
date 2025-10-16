"""
Mock urgency detector for demo purposes.
"""
import random
from typing import Tuple, Dict, Any

class UrgencyDetector:
    """Mock urgency detector that returns random urgency levels."""
    
    def __init__(self):
        self.urgency_levels = ["low", "medium", "high", "critical"]
    
    def predict(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict urgency for given text."""
        urgency = random.choice(self.urgency_levels)
        confidence = random.uniform(0.6, 0.9)
        
        if include_all_scores:
            scores = {level: random.uniform(0.1, 0.8) for level in self.urgency_levels}
            scores[urgency] = confidence
            return urgency, confidence, scores
        
        return urgency, confidence, {}