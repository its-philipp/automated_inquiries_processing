"""
Intelligent inquiry classifier that analyzes text content.
"""
import re
from typing import Tuple, Dict, Any

class InquiryClassifier:
    """Intelligent classifier that analyzes text content for keywords."""
    
    def __init__(self):
        self.categories = [
            "technical_support", "billing", "sales", "hr", "legal", "product_feedback"
        ]
        
        # Keyword mappings for each category
        self.keywords = {
            "technical_support": [
                "login", "password", "technical", "bug", "error", "issue", "problem", 
                "not working", "broken", "crash", "slow", "freeze", "troubleshoot",
                "support", "help", "fix", "repair", "technical", "system", "software",
                "hardware", "connection", "network", "server", "database", "api"
            ],
            "billing": [
                "bill", "invoice", "payment", "charge", "cost", "price", "fee", "refund",
                "subscription", "plan", "upgrade", "downgrade", "billing", "account",
                "credit", "debit", "transaction", "receipt", "money", "cost", "expensive"
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
        """Predict category based on text content analysis."""
        if not text:
            return "technical_support", 0.5, {}
        
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
            
            # Calculate confidence based on keyword density and uniqueness
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