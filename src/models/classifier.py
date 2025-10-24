"""
BERT-based inquiry classifier using Hugging Face transformers.
"""
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, Dict, Any
import logging
import os
from .model_cache import get_cached_classifier

logger = logging.getLogger(__name__)

class InquiryClassifier:
    """BERT-based classifier using zero-shot classification."""
    
    def __init__(self):
        self.categories = [
            "technical_support", "billing", "sales", "hr", "legal", "product_feedback"
        ]
        
        # Initialize the zero-shot classifier using cache
        try:
            # Check if running on macOS host - force keyword-based fallback for memory optimization
            # Docker containers run Linux, so we detect macOS via environment or hostname
            is_macos = (
                os.environ.get('HOST_OS') == 'Darwin' or 
                'mac' in os.environ.get('HOSTNAME', '').lower() or
                os.environ.get('MACOS_OPTIMIZATION', '').lower() == 'true'
            )
            
            if is_macos:
                logger.warning("🔄 macOS host detected - using keyword-based classifier for memory optimization")
                self.classifier = None
                self._init_keyword_fallback()
                logger.info("✅ Keyword-based classifier initialized successfully")
                return
            
            self.classifier = get_cached_classifier()
            if self.classifier is None:
                logger.warning("🔄 Failed to get cached classifier, initializing new one")
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-base-mnli",  # Smaller model (400MB vs 1.6GB)
                    device=0 if torch.cuda.is_available() else -1,
                    max_length=512,  # Limit input length to reduce memory usage
                    batch_size=1  # Process one at a time to reduce memory usage
                )
            logger.info("✅ BERT-based classifier initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize BERT classifier: {e}")
            logger.warning("🔄 Falling back to keyword-based classifier for macOS compatibility")
            # Fallback to keyword-based classifier
            self.classifier = None
            self._init_keyword_fallback()
    
    def _init_keyword_fallback(self):
        """Initialize keyword-based fallback classifier."""
        logger.warning("🔄 Falling back to keyword-based classifier")
        self.keywords = {
            "technical_support": [
                "login", "password", "technical", "bug", "error", "issue", "problem", 
                "not working", "broken", "crash", "slow", "freeze", "troubleshoot",
                "support", "help", "fix", "repair", "system", "software",
                "hardware", "connection", "network", "server", "database", "api"
            ],
            "billing": [
                "bill", "invoice", "payment", "charge", "cost", "price", "fee", "refund",
                "subscription", "plan", "upgrade", "downgrade", "billing", "account",
                "credit", "debit", "transaction", "receipt", "money", "expensive"
            ],
            "sales": [
                "buy", "purchase", "order", "quote", "demo", "trial", "pricing", "features",
                "compare", "interested", "sales", "new customer", "sign up", "register",
                "product", "service", "offer", "discount", "promotion", "deal"
            ],
            "hr": [
                "job", "career", "employment", "resume", "interview", "hiring", "position",
                "hr", "human resources", "benefits", "vacation", "time off", "policy",
                "employee", "staff", "team", "workplace", "office", "remote work"
            ],
            "legal": [
                "legal", "law", "terms", "conditions", "privacy", "policy", "agreement",
                "contract", "liability", "compliance", "regulation", "lawsuit", "court",
                "attorney", "lawyer", "rights", "copyright", "trademark", "intellectual"
            ],
            "product_feedback": [
                "feedback", "suggestion", "improvement", "feature request", "enhancement",
                "idea", "recommendation", "user experience", "ux", "ui", "design",
                "usability", "interface", "workflow", "process", "optimization"
            ]
        }
    
    def predict(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict category using BERT or keyword-based fallback."""
        if not text:
            return "technical_support", 0.5, {}
        
        # Use BERT classifier if available
        if self.classifier is not None:
            try:
                return self._predict_with_bert(text, include_all_scores)
            except Exception as e:
                logger.error(f"❌ BERT prediction failed: {e}")
                logger.warning("🔄 Falling back to keyword-based prediction")
                return self._predict_with_keywords(text, include_all_scores)
        else:
            return self._predict_with_keywords(text, include_all_scores)
    
    def _predict_with_bert(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Predict using BERT zero-shot classification."""
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
    
    def _predict_with_keywords(self, text: str, include_all_scores: bool = False) -> Tuple[str, float, Dict[str, float]]:
        """Fallback keyword-based prediction."""
        text_lower = text.lower()
        
        # Calculate scores for each category based on keyword matches
        category_scores = {}
        total_matches = 0
        
        for category, keywords in self.keywords.items():
            matches = 0
            for keyword in keywords:
                if keyword in text_lower:
                    matches += 1
                    total_matches += 1
            category_scores[category] = matches
        
        # If no keywords found, default to technical_support
        if total_matches == 0:
            category = "technical_support"
            confidence = 0.6
        else:
            # Find category with highest score
            category = max(category_scores, key=category_scores.get)
            max_matches = category_scores[category]
            
            # Calculate confidence based on keyword density
            confidence = min(0.95, 0.6 + (max_matches / max(1, len(text.split())) * 0.3))
        
        if include_all_scores:
            # Normalize scores for all categories
            all_scores = {}
            for cat in self.categories:
                if total_matches > 0:
                    all_scores[cat] = category_scores.get(cat, 0) / total_matches
                else:
                    all_scores[cat] = 0.1 if cat == category else 0.05
            return category, confidence, all_scores
        
        return category, confidence, {}