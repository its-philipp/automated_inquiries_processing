"""
Airflow DAG for batch classification of inquiries.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import sys
from pathlib import Path

# Mock implementations for demo (simplified for Airflow)
print("Using mock implementations for demo")

class InquiryClassifier:
    def predict(self, text, include_all_scores=False):
        import random
        categories = ["technical_support", "billing", "sales", "hr", "legal", "product_feedback"]
        return random.choice(categories), 0.85, {cat: 0.1 for cat in categories}

class SentimentAnalyzer:
    def predict(self, text, include_all_scores=False):
        import random
        sentiments = ["positive", "neutral", "negative"]
        return random.choice(sentiments), 0.80, {sent: 0.2 for sent in sentiments}

class UrgencyDetector:
    def predict(self, text, include_all_scores=False):
        import random
        urgency_levels = ["low", "medium", "high", "critical"]
        return random.choice(urgency_levels), 0.75, {level: 0.15 for level in urgency_levels}

class RoutingEngine:
    def route(self, inquiry_id, prediction):
        import random
        departments = ["technical_support", "billing", "sales", "hr", "legal"]
        consultants = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson"]
        return type('RoutingDecision', (), {
            'inquiry_id': inquiry_id,
            'department': random.choice(departments),
            'assigned_consultant': random.choice(consultants),
            'priority_score': random.uniform(1.0, 5.0),
            'escalated': random.choice([True, False]),
            'routing_reason': 'Demo routing decision'
        })()

class TextProcessor:
    def process(self, text):
        return text.strip()
    
    def process_inquiry(self, subject, body):
        """Process inquiry text for ML prediction."""
        cleaned_subject = subject.strip().lower() if subject else ""
        cleaned_body = body.strip().lower() if body else ""
        combined_text = f"{cleaned_subject} {cleaned_body}".strip()
        return cleaned_subject, cleaned_body, combined_text

# Mock enums
class InquiryCategory:
    TECHNICAL_SUPPORT = "technical_support"
    BILLING = "billing"
    SALES = "sales"
    HR = "hr"
    LEGAL = "legal"
    PRODUCT_FEEDBACK = "product_feedback"

class UrgencyLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SentimentType:
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'batch_classify_inquiries',
    default_args=default_args,
    description='Batch classification and routing of unprocessed inquiries',
    schedule_interval=timedelta(hours=1),  # Run every hour
    catchup=False,
    tags=['ml', 'classification', 'batch'],
)


def load_unprocessed_inquiries(**context):
    """Load unprocessed inquiries from database."""
    import psycopg2
    
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        database='inquiry_automation',
        user='postgres',
        password='postgres'
    )
    cursor = conn.cursor()
    
    query = """
        SELECT id, subject, body, sender_email, sender_name, timestamp
        FROM inquiries
        WHERE processed = FALSE
        LIMIT 1000
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    inquiries = []
    for row in results:
        inquiries.append({
            'id': row[0],
            'subject': row[1],
            'body': row[2],
            'sender_email': row[3],
            'sender_name': row[4],
            'timestamp': row[5],
        })
    
    cursor.close()
    conn.close()
    
    print(f"Loaded {len(inquiries)} unprocessed inquiries")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='inquiries', value=inquiries)
    return len(inquiries)


def classify_inquiries(**context):
    """Classify inquiries using ML models."""
    # Pull inquiries from XCom
    inquiries = context['task_instance'].xcom_pull(
        task_ids='load_unprocessed_inquiries',
        key='inquiries'
    )
    
    if not inquiries:
        print("No inquiries to classify")
        return 0
    
    # Initialize models
    text_processor = TextProcessor()
    classifier = InquiryClassifier()
    sentiment_analyzer = SentimentAnalyzer()
    urgency_detector = UrgencyDetector()
    
    predictions = []
    
    for inquiry in inquiries:
        # Preprocess
        cleaned_subject, cleaned_body, combined_text = text_processor.process_inquiry(
            inquiry['subject'],
            inquiry['body']
        )
        
        # Classify
        category, cat_conf, _ = classifier.predict(combined_text)
        sentiment, sent_conf, _ = sentiment_analyzer.predict(combined_text)
        urgency, urg_conf, _ = urgency_detector.predict(combined_text)
        
        predictions.append({
            'inquiry_id': inquiry['id'],
            'category': category,
            'category_confidence': cat_conf,
            'sentiment': sentiment,
            'sentiment_confidence': sent_conf,
            'urgency': urgency,
            'urgency_confidence': urg_conf,
        })
    
    print(f"Classified {len(predictions)} inquiries")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='predictions', value=predictions)
    return len(predictions)


def route_inquiries(**context):
    """Route inquiries to departments."""
    # Pull predictions from XCom
    predictions = context['task_instance'].xcom_pull(
        task_ids='classify_inquiries',
        key='predictions'
    )
    
    if not predictions:
        print("No predictions to route")
        return 0
    
    # Initialize routing engine
    routing_engine = RoutingEngine()
    
    routing_decisions = []
    
    # Mock PredictionResult class
    class PredictionResult:
        def __init__(self, inquiry_id, category, category_confidence, sentiment, sentiment_confidence, urgency, urgency_confidence, model_versions=None):
            self.inquiry_id = inquiry_id
            self.category = category
            self.category_confidence = category_confidence
            self.sentiment = sentiment
            self.sentiment_confidence = sentiment_confidence
            self.urgency = urgency
            self.urgency_confidence = urgency_confidence
            self.model_versions = model_versions or {}
    
    for pred in predictions:
        # Create prediction result object
        prediction_result = PredictionResult(
            inquiry_id=pred['inquiry_id'],
            category=pred['category'],  # Use string directly
            category_confidence=pred['category_confidence'],
            sentiment=pred['sentiment'],  # Use string directly
            sentiment_confidence=pred['sentiment_confidence'],
            urgency=pred['urgency'],  # Use string directly
            urgency_confidence=pred['urgency_confidence'],
            model_versions={'classifier': 'v1.0', 'sentiment': 'v1.0', 'urgency': 'v1.0'},
        )
        
        # Route
        routing = routing_engine.route(pred['inquiry_id'], prediction_result)
        
        routing_decisions.append({
            'inquiry_id': pred['inquiry_id'],
            'department': routing.department,  # Use string directly
            'assigned_consultant': routing.assigned_consultant,
            'priority_score': routing.priority_score,
            'escalated': routing.escalated,
            'routing_reason': routing.routing_reason,
        })
    
    print(f"Routed {len(routing_decisions)} inquiries")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='routing_decisions', value=routing_decisions)
    return len(routing_decisions)


def save_predictions_and_routing(**context):
    """Save predictions and routing decisions to database."""
    predictions = context['task_instance'].xcom_pull(
        task_ids='classify_inquiries',
        key='predictions'
    )
    
    routing_decisions = context['task_instance'].xcom_pull(
        task_ids='route_inquiries',
        key='routing_decisions'
    )
    
    if not predictions or not routing_decisions:
        print("No data to save")
        return 0
    
    import psycopg2
    
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        database='inquiry_automation',
        user='postgres',
        password='postgres'
    )
    cursor = conn.cursor()
    
    # Save predictions
    for pred in predictions:
        cursor.execute("""
            INSERT INTO predictions (
                inquiry_id, category, category_confidence,
                sentiment, sentiment_confidence,
                urgency, urgency_confidence,
                model_versions, predicted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (inquiry_id) DO UPDATE SET
                category = EXCLUDED.category,
                category_confidence = EXCLUDED.category_confidence,
                sentiment = EXCLUDED.sentiment,
                sentiment_confidence = EXCLUDED.sentiment_confidence,
                urgency = EXCLUDED.urgency,
                urgency_confidence = EXCLUDED.urgency_confidence
        """, (
            pred['inquiry_id'],
            pred['category'],
            pred['category_confidence'],
            pred['sentiment'],
            pred['sentiment_confidence'],
            pred['urgency'],
            pred['urgency_confidence'],
            '{"classifier": "v1.0", "sentiment": "v1.0", "urgency": "v1.0"}',
        ))
    
    # Save routing decisions
    for routing in routing_decisions:
        cursor.execute("""
            INSERT INTO routing_decisions (
                inquiry_id, department, assigned_consultant,
                priority_score, escalated, routing_reason,
                routed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (inquiry_id) DO UPDATE SET
                department = EXCLUDED.department,
                assigned_consultant = EXCLUDED.assigned_consultant,
                priority_score = EXCLUDED.priority_score,
                escalated = EXCLUDED.escalated,
                routing_reason = EXCLUDED.routing_reason
        """, (
            routing['inquiry_id'],
            routing['department'],
            routing['assigned_consultant'],
            routing['priority_score'],
            routing['escalated'],
            routing['routing_reason'],
        ))
    
    # Update inquiries as processed
    inquiry_ids = [p['inquiry_id'] for p in predictions]
    cursor.execute(f"""
        UPDATE inquiries
        SET processed = TRUE, processed_at = NOW()
        WHERE id = ANY(%s)
    """, (inquiry_ids,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Saved {len(predictions)} predictions and {len(routing_decisions)} routing decisions")
    return len(predictions)


# Define tasks
load_task = PythonOperator(
    task_id='load_unprocessed_inquiries',
    python_callable=load_unprocessed_inquiries,
    dag=dag,
)

classify_task = PythonOperator(
    task_id='classify_inquiries',
    python_callable=classify_inquiries,
    dag=dag,
)

route_task = PythonOperator(
    task_id='route_inquiries',
    python_callable=route_inquiries,
    dag=dag,
)

save_task = PythonOperator(
    task_id='save_predictions_and_routing',
    python_callable=save_predictions_and_routing,
    dag=dag,
)

# Define task dependencies
load_task >> classify_task >> route_task >> save_task

