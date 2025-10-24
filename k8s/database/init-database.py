#!/usr/bin/env python3
"""
Database initialization script for the inquiry automation pipeline.
Creates tables and inserts sample data.
"""
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import models
import sys
sys.path.append('/app')
sys.path.append('/app/src')
from database.models import Base, Inquiry, Prediction, Routing, ModelVersion, PerformanceMetric

def get_db_connection():
    """Create database connection."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@postgresql.inquiries-system.svc.cluster.local:5432/inquiry_automation"
    )
    engine = create_engine(db_url)
    return engine

def create_tables(engine):
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✅ Tables created successfully!")

def insert_sample_data(session):
    """Insert sample data for testing."""
    print("Inserting sample data...")
    
    # Sample inquiries
    sample_inquiries = [
        {
            "id": str(uuid.uuid4()),
            "subject": "Urgent: Server Down - Production Issue",
            "body": "Our production server has been down for 2 hours. Customers are unable to access our services. This is affecting our revenue significantly. Please help immediately!",
            "sender_email": "john.doe@techcorp.com",
            "sender_name": "John Doe",
            "timestamp": datetime.utcnow() - timedelta(hours=1),
            "processed": True,
            "processed_at": datetime.utcnow() - timedelta(minutes=30)
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Question about pricing plans",
            "body": "Hi, I'm interested in your premium plan but have some questions about the features. Could someone explain the differences between basic and premium?",
            "sender_email": "sarah.smith@example.com",
            "sender_name": "Sarah Smith",
            "timestamp": datetime.utcnow() - timedelta(hours=3),
            "processed": True,
            "processed_at": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Bug report: Login not working",
            "body": "I'm unable to log into my account. I keep getting an error message. This started happening yesterday. Please fix this issue.",
            "sender_email": "mike.wilson@company.com",
            "sender_name": "Mike Wilson",
            "timestamp": datetime.utcnow() - timedelta(hours=5),
            "processed": True,
            "processed_at": datetime.utcnow() - timedelta(hours=4)
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Feature request: Dark mode",
            "body": "Would it be possible to add a dark mode option to the application? Many users have requested this feature. It would improve the user experience significantly.",
            "sender_email": "lisa.brown@startup.io",
            "sender_name": "Lisa Brown",
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "processed": True,
            "processed_at": datetime.utcnow() - timedelta(hours=20)
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Billing inquiry",
            "body": "I noticed an unexpected charge on my credit card. Can someone help me understand what this charge is for? The amount is $99.99.",
            "sender_email": "robert.taylor@business.com",
            "sender_name": "Robert Taylor",
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "processed": True,
            "processed_at": datetime.utcnow() - timedelta(days=1, hours=12)
        }
    ]
    
    # Insert inquiries
    for inquiry_data in sample_inquiries:
        inquiry = Inquiry(**inquiry_data)
        session.add(inquiry)
    
    session.commit()
    print(f"✅ Inserted {len(sample_inquiries)} sample inquiries")
    
    # Sample predictions
    sample_predictions = [
        {
            "inquiry_id": sample_inquiries[0]["id"],
            "category": "technical_support",
            "category_confidence": 0.95,
            "sentiment": "urgent",
            "sentiment_confidence": 0.88,
            "urgency": "high",
            "urgency_confidence": 0.92,
            "model_versions": {"classifier": "v1.2", "sentiment": "v1.1", "urgency": "v1.3"},
            "predicted_at": datetime.utcnow() - timedelta(minutes=30)
        },
        {
            "inquiry_id": sample_inquiries[1]["id"],
            "category": "sales",
            "category_confidence": 0.87,
            "sentiment": "neutral",
            "sentiment_confidence": 0.76,
            "urgency": "low",
            "urgency_confidence": 0.82,
            "model_versions": {"classifier": "v1.2", "sentiment": "v1.1", "urgency": "v1.3"},
            "predicted_at": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "inquiry_id": sample_inquiries[2]["id"],
            "category": "technical_support",
            "category_confidence": 0.91,
            "sentiment": "frustrated",
            "sentiment_confidence": 0.83,
            "urgency": "medium",
            "urgency_confidence": 0.78,
            "model_versions": {"classifier": "v1.2", "sentiment": "v1.1", "urgency": "v1.3"},
            "predicted_at": datetime.utcnow() - timedelta(hours=4)
        },
        {
            "inquiry_id": sample_inquiries[3]["id"],
            "category": "feature_request",
            "category_confidence": 0.89,
            "sentiment": "positive",
            "sentiment_confidence": 0.85,
            "urgency": "low",
            "urgency_confidence": 0.71,
            "model_versions": {"classifier": "v1.2", "sentiment": "v1.1", "urgency": "v1.3"},
            "predicted_at": datetime.utcnow() - timedelta(hours=20)
        },
        {
            "inquiry_id": sample_inquiries[4]["id"],
            "category": "billing",
            "category_confidence": 0.93,
            "sentiment": "concerned",
            "sentiment_confidence": 0.79,
            "urgency": "medium",
            "urgency_confidence": 0.86,
            "model_versions": {"classifier": "v1.2", "sentiment": "v1.1", "urgency": "v1.3"},
            "predicted_at": datetime.utcnow() - timedelta(days=1, hours=12)
        }
    ]
    
    # Insert predictions
    for prediction_data in sample_predictions:
        prediction = Prediction(**prediction_data)
        session.add(prediction)
    
    session.commit()
    print(f"✅ Inserted {len(sample_predictions)} sample predictions")
    
    # Sample routing decisions
    sample_routing = [
        {
            "inquiry_id": sample_inquiries[0]["id"],
            "department": "technical_support",
            "assigned_consultant": "Alex Johnson",
            "priority_score": 0.95,
            "escalated": True,
            "routing_reason": "High urgency production issue",
            "status": "in_progress",
            "routed_at": datetime.utcnow() - timedelta(minutes=30)
        },
        {
            "inquiry_id": sample_inquiries[1]["id"],
            "department": "sales",
            "assigned_consultant": "Maria Garcia",
            "priority_score": 0.45,
            "escalated": False,
            "routing_reason": "Sales inquiry about pricing",
            "status": "resolved",
            "resolved_at": datetime.utcnow() - timedelta(hours=1),
            "routed_at": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "inquiry_id": sample_inquiries[2]["id"],
            "department": "technical_support",
            "assigned_consultant": "David Chen",
            "priority_score": 0.72,
            "escalated": False,
            "routing_reason": "Login issue reported",
            "status": "resolved",
            "resolved_at": datetime.utcnow() - timedelta(hours=2),
            "routed_at": datetime.utcnow() - timedelta(hours=4)
        },
        {
            "inquiry_id": sample_inquiries[3]["id"],
            "department": "product",
            "assigned_consultant": "Emma Wilson",
            "priority_score": 0.38,
            "escalated": False,
            "routing_reason": "Feature request for dark mode",
            "status": "pending",
            "routed_at": datetime.utcnow() - timedelta(hours=20)
        },
        {
            "inquiry_id": sample_inquiries[4]["id"],
            "department": "billing",
            "assigned_consultant": "Tom Anderson",
            "priority_score": 0.68,
            "escalated": False,
            "routing_reason": "Billing inquiry about charges",
            "status": "resolved",
            "resolved_at": datetime.utcnow() - timedelta(hours=6),
            "routed_at": datetime.utcnow() - timedelta(days=1, hours=12)
        }
    ]
    
    # Insert routing decisions
    for routing_data in sample_routing:
        routing = Routing(**routing_data)
        session.add(routing)
    
    session.commit()
    print(f"✅ Inserted {len(sample_routing)} sample routing decisions")
    
    # Sample model versions
    sample_models = [
        {
            "model_name": "classifier",
            "model_type": "BERT",
            "version": "v1.2",
            "mlflow_run_id": "run_001",
            "metrics": {"accuracy": 0.92, "f1_score": 0.89},
            "status": "production",
            "deployed_at": datetime.utcnow() - timedelta(days=7)
        },
        {
            "model_name": "sentiment",
            "model_type": "RoBERTa",
            "version": "v1.1",
            "mlflow_run_id": "run_002",
            "metrics": {"accuracy": 0.88, "f1_score": 0.85},
            "status": "production",
            "deployed_at": datetime.utcnow() - timedelta(days=10)
        },
        {
            "model_name": "urgency",
            "model_type": "BERT",
            "version": "v1.3",
            "mlflow_run_id": "run_003",
            "metrics": {"accuracy": 0.91, "f1_score": 0.87},
            "status": "production",
            "deployed_at": datetime.utcnow() - timedelta(days=5)
        }
    ]
    
    # Insert model versions
    for model_data in sample_models:
        model = ModelVersion(**model_data)
        session.add(model)
    
    session.commit()
    print(f"✅ Inserted {len(sample_models)} sample model versions")
    
    # Sample performance metrics
    sample_metrics = []
    for i in range(24):  # Last 24 hours
        timestamp = datetime.utcnow() - timedelta(hours=i)
        sample_metrics.extend([
            {
                "metric_name": "processing_latency",
                "metric_value": 0.5 + (i % 3) * 0.2,
                "metric_type": "latency",
                "recorded_at": timestamp
            },
            {
                "metric_name": "classification_accuracy",
                "metric_value": 0.90 + (i % 5) * 0.02,
                "metric_type": "accuracy",
                "model_name": "classifier",
                "recorded_at": timestamp
            },
            {
                "metric_name": "sentiment_accuracy",
                "metric_value": 0.85 + (i % 4) * 0.03,
                "metric_type": "accuracy",
                "model_name": "sentiment",
                "recorded_at": timestamp
            }
        ])
    
    # Insert performance metrics
    for metric_data in sample_metrics:
        metric = PerformanceMetric(**metric_data)
        session.add(metric)
    
    session.commit()
    print(f"✅ Inserted {len(sample_metrics)} sample performance metrics")

def main():
    """Main initialization function."""
    print("🚀 Initializing database for inquiry automation pipeline...")
    
    try:
        # Create engine and session
        engine = get_db_connection()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create tables
        create_tables(engine)
        
        # Insert sample data
        insert_sample_data(session)
        
        print("\n🎉 Database initialization completed successfully!")
        print("✅ All tables created")
        print("✅ Sample data inserted")
        print("✅ Ready for Streamlit dashboard!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
