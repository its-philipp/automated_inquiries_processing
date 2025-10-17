"""
BERT-based urgency detector using Hugging Face transformers.
"""
import torch
from transformers import pipeline
from typing import Tuple, Dict, Any
import logging
from .model_cache import get_cached_urgency_detector

logger = logging.getLogger(__name__)

class UrgencyDetector:
    """BERT-based urgency detector."""
    
    def __init__(self):
        self.urgency_levels = ["low", "medium", "high", "critical"]
        
        # Initialize the urgency detection pipeline using cache
        try:
            self.detector = get_cached_urgency_detector()
            if self.detector is None:
                logger.warning("🔄 Failed to get cached urgency detector, initializing new one")
                self.detector = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
            logger.info("✅ BERT-based urgency detector initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize BERT urgency detector: {e}")
            # Fallback to keyword-based detector
            self.detector = None
            self._init_keyword_fallback()
    
    def _init_keyword_fallback(self):
        """Initialize keyword-based fallback urgency detector."""
        logger.warning("🔄 Falling back to keyword-based urgency detector")
        self.urgency_keywords = {
            "critical": [
                "urgent", "emergency", "critical", "asap", "immediately", "now", "down", "broken",
                "not working", "system down", "production down", "outage", "security breach",
                "data loss", "hack", "breach", "compromise", "critical bug", "severe",
                "escalate", "manager", "director", "ceo", "executive", "priority 1"
            ],
            "high": [
                "important", "soon", "today", "deadline", "due", "escalate", "manager",
                "priority", "high", "significant", "major", "serious", "concern",
                "issue", "problem", "bug", "error", "failing", "not working properly"
            ],
            "medium": [
                "when possible", "this week", "moderate", "somewhat", "minor", "small",
                "question", "inquiry", "information", "clarification", "help", "support"
            ],
            "low": [
                "when convenient", "no rush", "low priority", "minor", "small", "question",
                "curiosity", "general", "information", "future", "someday", "eventually"
            ]
        }
    
    def predict(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict urgency using BERT or keyword-based fallback."""
        if not text:
            return "medium", 0.5, {}
        
        # Use BERT detector if available
        if self.detector is not None:
            try:
                return self._predict_with_bert(text, include_all_scores)
            except Exception as e:
                logger.error(f"❌ BERT urgency prediction failed: {e}")
                logger.warning("🔄 Falling back to keyword-based prediction")
                return self._predict_with_keywords(text, include_all_scores)
        else:
            return self._predict_with_keywords(text, include_all_scores)
    
    def _predict_with_bert(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict urgency using BERT zero-shot classification."""
        # Prepare candidate labels with descriptions
        candidate_labels = [
            "low priority inquiry that can be handled when convenient",
            "medium priority question that needs attention this week", 
            "high priority issue that requires prompt attention",
            "critical emergency that needs immediate resolution"
        ]
        
        # Run zero-shot classification
        result = self.detector(text, candidate_labels)
        
        # Map result to our urgency levels
        label_mapping = {
            "low priority inquiry that can be handled when convenient": "low",
            "medium priority question that needs attention this week": "medium",
            "high priority issue that requires prompt attention": "high", 
            "critical emergency that needs immediate resolution": "critical"
        }
        
        urgency = label_mapping.get(result['labels'][0], "medium")
        confidence = result['scores'][0]
        
        if include_all_scores:
            all_scores = {}
            for i, label in enumerate(result['labels']):
                urg = label_mapping.get(label, "medium")
                all_scores[urg] = result['scores'][i]
            return urgency, confidence, all_scores
        
        return urgency, confidence, {}
    
    def _predict_with_keywords(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Fallback keyword-based urgency prediction."""
        text_lower = text.lower()
        
        # Calculate scores for each urgency level based on keyword matches
        urgency_scores = {}
        total_matches = 0
        
        for urgency, keywords in self.urgency_keywords.items():
            matches = 0
            for keyword in keywords:
                if keyword in text_lower:
                    matches += 1
                    total_matches += 1
            urgency_scores[urgency] = matches
        
        # If no keywords found, default to medium
        if total_matches == 0:
            urgency = "medium"
            confidence = 0.6
        else:
            # Find urgency level with highest score
            urgency = max(urgency_scores, key=urgency_scores.get)
            max_matches = urgency_scores[urgency]
            
            # Calculate confidence based on keyword density
            confidence = min(0.95, 0.6 + (max_matches / max(1, len(text.split())) * 0.3))
        
        if include_all_scores:
            # Normalize scores for all urgency levels
            all_scores = {}
            for urg in self.urgency_levels:
                if total_matches > 0:
                    all_scores[urg] = urgency_scores.get(urg, 0) / total_matches
                else:
                    all_scores[urg] = 0.1 if urg == urgency else 0.05
            return urgency, confidence, all_scores
        
        return urgency, confidence, {}