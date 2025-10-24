#!/usr/bin/env python3
"""
Simple database initialization script using raw SQL.
"""
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

def get_db_connection():
    """Create database connection."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@postgresql.inquiries-system.svc.cluster.local:5432/inquiry_automation"
    )
    engine = create_engine(db_url)
    return engine

def create_tables(engine):
    """Create all database tables using raw SQL."""
    print("Creating database tables...")
    
    with engine.connect() as conn:
        # Create inquiries table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inquiries (
                id VARCHAR(36) PRIMARY KEY,
                subject VARCHAR(500) NOT NULL,
                body TEXT NOT NULL,
                sender_email VARCHAR(255) NOT NULL,
                sender_name VARCHAR(255),
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                meta_data JSONB DEFAULT '{}',
                processed BOOLEAN DEFAULT FALSE,
                processed_at TIMESTAMP
            )
        """))
        
        # Create indexes for inquiries
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sender_email ON inquiries (sender_email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_timestamp ON inquiries (timestamp)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_processed ON inquiries (processed)"))
        
        # Create predictions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                inquiry_id VARCHAR(36) NOT NULL UNIQUE REFERENCES inquiries(id),
                category VARCHAR(50) NOT NULL,
                category_confidence FLOAT NOT NULL,
                sentiment VARCHAR(20) NOT NULL,
                sentiment_confidence FLOAT NOT NULL,
                urgency VARCHAR(20) NOT NULL,
                urgency_confidence FLOAT NOT NULL,
                model_versions JSONB DEFAULT '{}',
                predicted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes for predictions
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_category ON predictions (category)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sentiment ON predictions (sentiment)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_urgency ON predictions (urgency)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_predicted_at ON predictions (predicted_at)"))
        
        # Create routing_decisions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS routing_decisions (
                id SERIAL PRIMARY KEY,
                inquiry_id VARCHAR(36) NOT NULL UNIQUE REFERENCES inquiries(id),
                department VARCHAR(50) NOT NULL,
                assigned_consultant VARCHAR(255),
                priority_score FLOAT NOT NULL,
                escalated BOOLEAN DEFAULT FALSE,
                routing_reason TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                resolved_at TIMESTAMP,
                routed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes for routing_decisions
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_department ON routing_decisions (department)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_status ON routing_decisions (status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_priority_score ON routing_decisions (priority_score)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_assigned_consultant ON routing_decisions (assigned_consultant)"))
        
        # Create model_versions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_versions (
                id SERIAL PRIMARY KEY,
                model_name VARCHAR(100) NOT NULL,
                model_type VARCHAR(100) NOT NULL,
                version VARCHAR(50) NOT NULL,
                mlflow_run_id VARCHAR(100),
                metrics JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'staging',
                deployed_at TIMESTAMP,
                archived_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                meta_data JSONB DEFAULT '{}'
            )
        """))
        
        # Create indexes for model_versions
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_model_name ON model_versions (model_name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_status ON model_versions (status)"))
        
        # Create performance_metrics table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                model_name VARCHAR(100),
                department VARCHAR(50),
                category VARCHAR(50),
                recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                meta_data JSONB DEFAULT '{}'
            )
        """))
        
        # Create indexes for performance_metrics
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_metric_name ON performance_metrics (metric_name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_recorded_at ON performance_metrics (recorded_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_model_name ON performance_metrics (model_name)"))
        
        conn.commit()
    
    print("✅ Tables created successfully!")

def insert_sample_data(engine):
    """Insert sample data for testing."""
    print("Inserting sample data...")
    
    with engine.connect() as conn:
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
        for inquiry in sample_inquiries:
            conn.execute(text("""
                INSERT INTO inquiries (id, subject, body, sender_email, sender_name, timestamp, processed, processed_at)
                VALUES (:id, :subject, :body, :sender_email, :sender_name, :timestamp, :processed, :processed_at)
            """), inquiry)
        
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
                "predicted_at": datetime.utcnow() - timedelta(days=1, hours=12)
            }
        ]
        
        # Insert predictions
        for prediction in sample_predictions:
            conn.execute(text("""
                INSERT INTO predictions (inquiry_id, category, category_confidence, sentiment, sentiment_confidence, urgency, urgency_confidence, predicted_at)
                VALUES (:inquiry_id, :category, :category_confidence, :sentiment, :sentiment_confidence, :urgency, :urgency_confidence, :predicted_at)
            """), prediction)
        
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
        for routing in sample_routing:
            # Handle NULL resolved_at values
            resolved_at = routing.get('resolved_at')
            conn.execute(text("""
                INSERT INTO routing_decisions (inquiry_id, department, assigned_consultant, priority_score, escalated, routing_reason, status, resolved_at, routed_at)
                VALUES (:inquiry_id, :department, :assigned_consultant, :priority_score, :escalated, :routing_reason, :status, :resolved_at, :routed_at)
            """), {
                'inquiry_id': routing['inquiry_id'],
                'department': routing['department'],
                'assigned_consultant': routing['assigned_consultant'],
                'priority_score': routing['priority_score'],
                'escalated': routing['escalated'],
                'routing_reason': routing['routing_reason'],
                'status': routing['status'],
                'resolved_at': resolved_at,
                'routed_at': routing['routed_at']
            })
        
        conn.commit()
    
    print("✅ Sample data inserted successfully!")

def main():
    """Main initialization function."""
    print("🚀 Initializing database for inquiry automation pipeline...")
    
    try:
        # Create engine
        engine = get_db_connection()
        
        # Create tables
        create_tables(engine)
        
        # Insert sample data
        insert_sample_data(engine)
        
        print("\n🎉 Database initialization completed successfully!")
        print("✅ All tables created")
        print("✅ Sample data inserted")
        print("✅ Ready for Streamlit dashboard!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        raise

if __name__ == "__main__":
    main()
