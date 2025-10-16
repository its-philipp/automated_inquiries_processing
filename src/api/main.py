"""
FastAPI application for the inquiry automation pipeline.
"""
import time
import uuid
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.schemas import (
    IncomingInquiry,
    ProcessedInquiry,
    PredictionResult,
    RoutingDecision,
    HealthCheck,
    APIResponse,
    InquiryCategory,
    UrgencyLevel,
    SentimentType,
    Department,
)
from src.database.connection import get_db, get_db_manager
from src.database.models import Inquiry, Prediction, Routing
from src.preprocessing.text_processor import TextProcessor
from src.models.classifier import InquiryClassifier
from src.models.sentiment import SentimentAnalyzer
from src.models.urgency import UrgencyDetector
from src.routing.router import RoutingEngine
from src.monitoring.real_metrics import metrics_collector


# Initialize components
text_processor = TextProcessor()
classifier = None
sentiment_analyzer = None
urgency_detector = None
routing_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    global classifier, sentiment_analyzer, urgency_detector, routing_engine
    
    print("Initializing models...")
    classifier = InquiryClassifier()
    sentiment_analyzer = SentimentAnalyzer()
    urgency_detector = UrgencyDetector()
    routing_engine = RoutingEngine()
    
    print("Creating database tables...")
    db_manager = get_db_manager()
    db_manager.create_tables()
    
    print("Application startup complete!")
    metrics_collector.set_system_health("api", True)
    metrics_collector.set_system_health("models", True)
    metrics_collector.set_system_health("database", True)
    
    yield
    
    # Shutdown
    print("Application shutdown")


# Create FastAPI app
app = FastAPI(
    title="Inquiry Automation Pipeline API",
    description="Intelligent automation pipeline for client inquiry classification and routing",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request timing and metrics
@app.middleware("http")
async def add_metrics_middleware(request, call_next):
    """Add metrics collection to all requests."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    metrics_collector.record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration=duration,
    )
    
    return response


# Health check endpoint
@app.get("/api/v1/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Check API health status."""
    services = {
        "api": True,
        "models": classifier is not None,
        "database": True,
        "routing": routing_engine is not None,
    }
    
    return HealthCheck(
        status="healthy" if all(services.values()) else "degraded",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        services=services,
    )


# Metrics endpoint for Prometheus
@app.get("/api/v1/metrics", tags=["Monitoring"])
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Submit inquiry endpoint
@app.post(
    "/api/v1/inquiries/submit",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Inquiries"]
)
async def submit_inquiry(
    inquiry: IncomingInquiry,
    db: Session = Depends(get_db)
):
    """
    Submit a new inquiry for processing.
    
    This endpoint receives an inquiry, processes it through the ML pipeline,
    and returns routing decision.
    """
    start_time = time.time()
    inquiry_id = str(uuid.uuid4())
    
    try:
        # Record inquiry received
        metrics_collector.record_inquiry_received("api")
        
        # Preprocess text
        cleaned_subject, cleaned_body, combined_text = text_processor.process_inquiry(
            inquiry.subject,
            inquiry.body
        )
        
        # Run model predictions
        category, cat_conf, _ = classifier.predict(combined_text)
        sentiment, sent_conf, _ = sentiment_analyzer.predict(combined_text)
        urgency, urg_conf, _ = urgency_detector.predict(combined_text)
        
        # Record model predictions
        metrics_collector.record_model_inference(
            "classifier", "category", category, cat_conf, 0.1
        )
        metrics_collector.record_model_inference(
            "sentiment", "sentiment", sentiment, sent_conf, 0.1
        )
        metrics_collector.record_model_inference(
            "urgency", "urgency", urgency, urg_conf, 0.1
        )
        metrics_collector.update_prediction_distributions(category, urgency, sentiment)
        
        # Create prediction result
        prediction_result = PredictionResult(
            inquiry_id=inquiry_id,
            category=InquiryCategory(category),
            category_confidence=cat_conf,
            sentiment=SentimentType(sentiment),
            sentiment_confidence=sent_conf,
            urgency=UrgencyLevel(urgency),
            urgency_confidence=urg_conf,
            model_versions={
                "classifier": "v1.0",
                "sentiment": "v1.0",
                "urgency": "v1.0",
            }
        )
        
        # Route inquiry
        routing_decision = routing_engine.route(inquiry_id, prediction_result)
        
        # Record routing metrics
        metrics_collector.record_routing_decision(
            department=routing_decision.department.value,
            priority_score=routing_decision.priority_score,
            escalated=routing_decision.escalated,
            consultant=routing_decision.assigned_consultant,
        )
        
        # Save to database
        db_inquiry = Inquiry(
            id=inquiry_id,
            subject=inquiry.subject,
            body=inquiry.body,
            sender_email=inquiry.sender_email,
            sender_name=inquiry.sender_name,
            timestamp=inquiry.timestamp,
            metadata=inquiry.metadata,
            processed=True,
            processed_at=datetime.utcnow(),
        )
        
        db_prediction = Prediction(
            inquiry_id=inquiry_id,
            category=prediction_result.category.value,
            category_confidence=prediction_result.category_confidence,
            sentiment=prediction_result.sentiment.value,
            sentiment_confidence=prediction_result.sentiment_confidence,
            urgency=prediction_result.urgency.value,
            urgency_confidence=prediction_result.urgency_confidence,
            model_versions=prediction_result.model_versions,
        )
        
        db_routing = Routing(
            inquiry_id=inquiry_id,
            department=routing_decision.department.value,
            assigned_consultant=routing_decision.assigned_consultant,
            priority_score=routing_decision.priority_score,
            escalated=routing_decision.escalated,
            routing_reason=routing_decision.routing_reason,
        )
        
        db.add(db_inquiry)
        db.add(db_prediction)
        db.add(db_routing)
        db.commit()
        
        # Record success
        duration = time.time() - start_time
        metrics_collector.record_inquiry_processed("success", duration)
        
        return APIResponse(
            success=True,
            message="Inquiry processed successfully",
            data={
                "inquiry_id": inquiry_id,
                "category": category,
                "urgency": urgency,
                "sentiment": sentiment,
                "department": routing_decision.department.value,
                "consultant": routing_decision.assigned_consultant,
                "priority_score": routing_decision.priority_score,
                "escalated": routing_decision.escalated,
            }
        )
    
    except Exception as e:
        # Record error
        duration = time.time() - start_time
        metrics_collector.record_inquiry_processed("failed", duration)
        metrics_collector.record_pipeline_error("inquiry_processing", type(e).__name__)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing inquiry: {str(e)}"
        )


# Get inquiry status endpoint
@app.get("/api/v1/inquiries/{inquiry_id}", tags=["Inquiries"])
async def get_inquiry_status(
    inquiry_id: str,
    db: Session = Depends(get_db)
):
    """Get status and details of a specific inquiry."""
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inquiry {inquiry_id} not found"
        )
    
    # Get associated prediction and routing
    prediction = db.query(Prediction).filter(Prediction.inquiry_id == inquiry_id).first()
    routing = db.query(Routing).filter(Routing.inquiry_id == inquiry_id).first()
    
    return {
        "inquiry_id": inquiry.id,
        "subject": inquiry.subject,
        "sender_email": inquiry.sender_email,
        "timestamp": inquiry.timestamp,
        "processed": inquiry.processed,
        "prediction": {
            "category": prediction.category if prediction else None,
            "urgency": prediction.urgency if prediction else None,
            "sentiment": prediction.sentiment if prediction else None,
        } if prediction else None,
        "routing": {
            "department": routing.department if routing else None,
            "consultant": routing.assigned_consultant if routing else None,
            "priority_score": routing.priority_score if routing else None,
            "escalated": routing.escalated if routing else None,
            "status": routing.status if routing else None,
        } if routing else None,
    }


# Classify text endpoint (without routing)
@app.post("/api/v1/inquiries/classify", tags=["Inquiries"])
async def classify_text(
    text: str,
    include_all_scores: bool = False
):
    """
    Classify text without saving to database.
    
    Useful for testing or preview purposes.
    """
    try:
        # Preprocess
        cleaned_text = text_processor.clean_text(text)
        
        # Classify
        category, cat_conf, cat_scores = classifier.predict(cleaned_text, include_all_scores)
        sentiment, sent_conf, sent_scores = sentiment_analyzer.predict(cleaned_text, include_all_scores)
        urgency, urg_conf, urg_scores = urgency_detector.predict(cleaned_text, include_all_scores)
        
        result = {
            "category": category,
            "category_confidence": cat_conf,
            "sentiment": sentiment,
            "sentiment_confidence": sent_conf,
            "urgency": urgency,
            "urgency_confidence": urg_conf,
        }
        
        if include_all_scores:
            result["all_scores"] = {
                "category": cat_scores,
                "sentiment": sent_scores,
                "urgency": urg_scores,
            }
        
        return result
    
    except Exception as e:
        metrics_collector.record_pipeline_error("classification", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error classifying text: {str(e)}"
        )


# Get statistics endpoint
@app.get("/api/v1/stats", tags=["Analytics"])
async def get_stats(
    db: Session = Depends(get_db),
    days: int = 7
):
    """Get pipeline statistics."""
    # Count total inquiries
    total_inquiries = db.query(Inquiry).count()
    processed_inquiries = db.query(Inquiry).filter(Inquiry.processed == True).count()
    
    # Get category distribution
    category_counts = {}
    for pred in db.query(Prediction).all():
        category_counts[pred.category] = category_counts.get(pred.category, 0) + 1
    
    # Get department distribution
    department_counts = {}
    for routing in db.query(Routing).all():
        department_counts[routing.department] = department_counts.get(routing.department, 0) + 1
    
    # Escalation count
    escalated_count = db.query(Routing).filter(Routing.escalated == True).count()
    
    return {
        "total_inquiries": total_inquiries,
        "processed_inquiries": processed_inquiries,
        "processing_rate": f"{(processed_inquiries/total_inquiries*100):.1f}%" if total_inquiries > 0 else "0%",
        "category_distribution": category_counts,
        "department_distribution": department_counts,
        "escalated_inquiries": escalated_count,
        "escalation_rate": f"{(escalated_count/total_inquiries*100):.1f}%" if total_inquiries > 0 else "0%",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

