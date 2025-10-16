"""
Mock routing engine for demo purposes.
"""
import random
from typing import Dict, Any
from src.schemas import PredictionResult, RoutingDecision, Department

class RoutingEngine:
    """Mock routing engine that assigns inquiries to departments."""
    
    def __init__(self):
        self.department_mapping = {
            "technical_support": Department.TECHNICAL_SUPPORT,
            "billing": Department.FINANCE,
            "sales": Department.SALES,
            "hr": Department.HR,
            "legal": Department.LEGAL,
            "product_feedback": Department.PRODUCT_MANAGEMENT,
        }
        self.consultants = {
            Department.TECHNICAL_SUPPORT: ["Alice Johnson", "Bob Smith"],
            Department.FINANCE: ["Carol Davis", "David Wilson"],
            Department.SALES: ["Eva Brown", "Frank Miller"],
            Department.HR: ["Grace Lee", "Henry Taylor"],
            Department.LEGAL: ["Ivy Chen", "Jack Anderson"],
            Department.PRODUCT_MANAGEMENT: ["Kate Rodriguez", "Liam Thompson"],
        }
    
    def route(self, inquiry_id: str, prediction: PredictionResult) -> RoutingDecision:
        """Route inquiry based on prediction results."""
        department = self.department_mapping.get(prediction.category.value, Department.TECHNICAL_SUPPORT)
        consultant = random.choice(self.consultants[department])
        
        # Calculate priority score based on urgency and sentiment
        urgency_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        sentiment_scores = {"positive": 1, "neutral": 2, "negative": 3}
        
        priority_score = (
            urgency_scores.get(prediction.urgency.value, 2) +
            sentiment_scores.get(prediction.sentiment.value, 2)
        ) / 2
        
        # Determine if escalation is needed
        escalated = (
            prediction.urgency.value == "critical" or
            prediction.sentiment.value == "negative" and prediction.urgency.value == "high"
        )
        
        routing_reason = f"Routed to {department.value} based on {prediction.category.value} category"
        
        return RoutingDecision(
            inquiry_id=inquiry_id,
            department=department,
            assigned_consultant=consultant,
            priority_score=priority_score,
            escalated=escalated,
            routing_reason=routing_reason,
        )