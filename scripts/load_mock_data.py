#!/usr/bin/env python3
"""
Load mock data into the database.
"""
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, Inquiry, Prediction, Routing
from src.database.connection import get_database_url

def load_mock_data():
    """Load mock data from JSON file into database."""
    print("Loading mock data into database...")
    
    # Get database URL
    db_url = get_database_url()
    print(f"Connecting to database: {db_url}")
    
    # Create engine and session
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Load mock data
    mock_data_path = Path("/app/sample_inquiries.json")
    
    if not mock_data_path.exists():
        print(f"❌ Mock data file not found: {mock_data_path}")
        return
    
    with open(mock_data_path, 'r', encoding='utf-8') as f:
        mock_inquiries = json.load(f)
    
    print(f"Found {len(mock_inquiries)} mock inquiries")
    
    # Create session
    session = SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        session.query(Routing).delete()
        session.query(Prediction).delete()
        session.query(Inquiry).delete()
        session.commit()
        
        # Load mock data
        for i, inquiry_data in enumerate(mock_inquiries):
            if i % 100 == 0:
                print(f"Processing inquiry {i+1}/{len(mock_inquiries)}")
            
            # Create inquiry
            inquiry_id = str(uuid.uuid4())
            inquiry = Inquiry(
                id=inquiry_id,
                subject=inquiry_data['subject'],
                body=inquiry_data['body'],
                sender_email=inquiry_data['sender_email'],
                sender_name=inquiry_data.get('sender_name'),
                timestamp=datetime.fromisoformat(inquiry_data['timestamp'].replace('Z', '+00:00')),
                meta_data=inquiry_data.get('metadata', {}),
                processed=True,
                processed_at=datetime.utcnow(),
            )
            
            # Create prediction
            prediction = Prediction(
                inquiry_id=inquiry_id,
                category=inquiry_data['metadata']['category'],
                category_confidence=0.85,  # Mock confidence
                sentiment=inquiry_data['metadata']['sentiment'],
                sentiment_confidence=0.80,
                urgency=inquiry_data['metadata']['urgency'],
                urgency_confidence=0.75,
                model_versions={
                    "classifier": "v1.0",
                    "sentiment": "v1.0",
                    "urgency": "v1.0",
                }
            )
            
            # Create routing
            department_mapping = {
                "technical_support": "technical_support",
                "billing": "finance",
                "sales": "sales",
                "hr": "hr",
                "legal": "legal",
                "product_feedback": "product_management",
            }
            
            department = department_mapping.get(inquiry_data['metadata']['category'], 'technical_support')
            
            # Simple consultant assignment
            consultants = {
                "technical_support": ["Alice Johnson", "Bob Smith"],
                "finance": ["Carol Davis", "David Wilson"],
                "sales": ["Eva Brown", "Frank Miller"],
                "hr": ["Grace Lee", "Henry Taylor"],
                "legal": ["Ivy Chen", "Jack Anderson"],
                "product_management": ["Kate Rodriguez", "Liam Thompson"],
            }
            
            consultant = consultants.get(department, ["Alice Johnson"])[i % len(consultants.get(department, ["Alice Johnson"]))]
            
            # Calculate priority score
            urgency_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            sentiment_scores = {"positive": 1, "neutral": 2, "negative": 3}
            
            priority_score = (
                urgency_scores.get(inquiry_data['metadata']['urgency'], 2) +
                sentiment_scores.get(inquiry_data['metadata']['sentiment'], 2)
            ) / 2
            
            # Determine escalation
            escalated = (
                inquiry_data['metadata']['urgency'] == "critical" or
                (inquiry_data['metadata']['sentiment'] == "negative" and inquiry_data['metadata']['urgency'] == "high")
            )
            
            routing = Routing(
                inquiry_id=inquiry_id,
                department=department,
                assigned_consultant=consultant,
                priority_score=priority_score,
                escalated=escalated,
                routing_reason=f"Routed to {department} based on {inquiry_data['metadata']['category']} category",
            )
            
            # Add to session
            session.add(inquiry)
            session.add(prediction)
            session.add(routing)
        
        # Commit all changes
        session.commit()
        print(f"✅ Successfully loaded {len(mock_inquiries)} inquiries into database!")
        
    except Exception as e:
        print(f"❌ Error loading mock data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    load_mock_data()
