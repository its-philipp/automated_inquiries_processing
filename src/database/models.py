"""
SQLAlchemy database models for the inquiry automation pipeline.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Inquiry(Base):
    """Incoming inquiry model."""
    
    __tablename__ = "inquiries"
    
    id = Column(String(36), primary_key=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    sender_email = Column(String(255), nullable=False, index=True)
    sender_name = Column(String(255))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    meta_data = Column(JSON, default={})
    
    # Processing status
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="inquiry", uselist=False)
    routing = relationship("Routing", back_populates="inquiry", uselist=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_sender_timestamp', 'sender_email', 'timestamp'),
        Index('idx_processed_timestamp', 'processed', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Inquiry(id={self.id}, subject={self.subject[:50]})>"


class Prediction(Base):
    """Model prediction results."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inquiry_id = Column(String(36), ForeignKey('inquiries.id'), nullable=False, unique=True)
    
    # Predictions
    category = Column(String(50), nullable=False, index=True)
    category_confidence = Column(Float, nullable=False)
    sentiment = Column(String(20), nullable=False, index=True)
    sentiment_confidence = Column(Float, nullable=False)
    urgency = Column(String(20), nullable=False, index=True)
    urgency_confidence = Column(Float, nullable=False)
    
    # Model versions
    model_versions = Column(JSON, default={})
    
    # Metadata
    predicted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationship
    inquiry = relationship("Inquiry", back_populates="predictions")
    
    __table_args__ = (
        Index('idx_category_urgency', 'category', 'urgency'),
        Index('idx_sentiment_urgency', 'sentiment', 'urgency'),
    )
    
    def __repr__(self):
        return f"<Prediction(inquiry_id={self.inquiry_id}, category={self.category})>"


class Routing(Base):
    """Routing decisions."""
    
    __tablename__ = "routing_decisions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inquiry_id = Column(String(36), ForeignKey('inquiries.id'), nullable=False, unique=True)
    
    # Routing
    department = Column(String(50), nullable=False, index=True)
    assigned_consultant = Column(String(255), index=True)
    priority_score = Column(Float, nullable=False, index=True)
    escalated = Column(Boolean, default=False, index=True)
    routing_reason = Column(Text)
    
    # Status tracking
    status = Column(String(20), default='pending', index=True)  # pending, in_progress, resolved, closed
    resolved_at = Column(DateTime)
    
    # Metadata
    routed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationship
    inquiry = relationship("Inquiry", back_populates="routing")
    
    __table_args__ = (
        Index('idx_department_status', 'department', 'status'),
        Index('idx_priority_status', 'priority_score', 'status'),
        Index('idx_consultant_status', 'assigned_consultant', 'status'),
    )
    
    def __repr__(self):
        return f"<Routing(inquiry_id={self.inquiry_id}, department={self.department})>"


class ModelVersion(Base):
    """Track model versions used in production."""
    
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, index=True)  # classifier, sentiment, urgency
    model_type = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    mlflow_run_id = Column(String(100))
    
    # Performance metrics
    metrics = Column(JSON, default={})
    
    # Status
    status = Column(String(20), default='staging', index=True)  # staging, production, archived
    deployed_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    meta_data = Column(JSON, default={})
    
    __table_args__ = (
        Index('idx_model_status', 'model_name', 'status'),
    )
    
    def __repr__(self):
        return f"<ModelVersion(name={self.model_name}, version={self.version}, status={self.status})>"


class PerformanceMetric(Base):
    """Track system and model performance metrics over time."""
    
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # latency, accuracy, throughput, etc.
    
    # Context
    model_name = Column(String(100), index=True)
    department = Column(String(50))
    category = Column(String(50))
    
    # Metadata
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    meta_data = Column(JSON, default={})
    
    __table_args__ = (
        Index('idx_metric_time', 'metric_name', 'recorded_at'),
        Index('idx_model_metric', 'model_name', 'metric_name', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<PerformanceMetric(name={self.metric_name}, value={self.metric_value})>"

