"""
Pydantic schemas for data validation throughout the pipeline.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator


class InquiryCategory(str, Enum):
    """Categories for client inquiries."""
    TECHNICAL_SUPPORT = "technical_support"
    BILLING = "billing"
    SALES = "sales"
    HR = "hr"
    LEGAL = "legal"
    PRODUCT_FEEDBACK = "product_feedback"


class UrgencyLevel(str, Enum):
    """Urgency levels for inquiries."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SentimentType(str, Enum):
    """Sentiment types."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Department(str, Enum):
    """Departments for routing."""
    TECHNICAL_SUPPORT = "technical_support"
    FINANCE = "finance"
    SALES = "sales"
    HR = "hr"
    LEGAL = "legal"
    PRODUCT_MANAGEMENT = "product_management"
    ESCALATION = "escalation"


class IncomingInquiry(BaseModel):
    """Schema for raw incoming inquiries."""
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1, max_length=10000)
    sender_email: EmailStr
    sender_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('body', 'subject')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip()


class ProcessedInquiry(BaseModel):
    """Schema for processed inquiries after text cleaning."""
    inquiry_id: str
    subject_cleaned: str
    body_cleaned: str
    combined_text: str
    sender_email: EmailStr
    sender_name: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PredictionResult(BaseModel):
    """Schema for model prediction outputs."""
    inquiry_id: str
    category: InquiryCategory
    category_confidence: float = Field(..., ge=0.0, le=1.0)
    sentiment: SentimentType
    sentiment_confidence: float = Field(..., ge=0.0, le=1.0)
    urgency: UrgencyLevel
    urgency_confidence: float = Field(..., ge=0.0, le=1.0)
    predicted_at: datetime = Field(default_factory=datetime.utcnow)
    model_versions: Dict[str, str] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Schema for final routing decisions."""
    inquiry_id: str
    department: Department
    assigned_consultant: Optional[str] = None
    priority_score: float = Field(..., ge=0.0, le=100.0)
    escalated: bool = False
    routing_reason: str
    routed_at: datetime = Field(default_factory=datetime.utcnow)


class InquiryWithPredictions(BaseModel):
    """Combined schema with inquiry and predictions."""
    inquiry: IncomingInquiry
    predictions: Optional[PredictionResult] = None
    routing: Optional[RoutingDecision] = None


class HealthCheck(BaseModel):
    """Schema for health check responses."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    services: Dict[str, bool]


class APIResponse(BaseModel):
    """Generic API response schema."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

