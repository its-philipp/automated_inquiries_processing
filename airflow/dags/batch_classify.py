"""
Airflow DAG for batch classification of inquiries.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import sys
from pathlib import Path

# Import real implementations
import sys
sys.path.append('/opt/airflow/src')

from models.classifier import InquiryClassifier
from models.sentiment import SentimentAnalyzer  
from models.urgency import UrgencyDetector
from routing.router import RoutingEngine
from schemas import PredictionResult, RoutingDecision, Department, InquiryCategory, UrgencyLevel, SentimentType
import yaml
import os

print("Using real BERT models and routing logic")

# Load routing configuration
def load_routing_config():
    """Load routing configuration from YAML file."""
    config_path = '/opt/airflow/config/routing_rules.yaml'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        print("Warning: routing_rules.yaml not found, using defaults")
        return {}

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
    'retries': 1,  # Reduced retries
    'retry_delay': timedelta(minutes=10),  # Longer retry delay
    'execution_timeout': timedelta(minutes=30),  # Increased timeout for ML tasks (BERT model downloads)
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
    """Classify inquiries using real BERT models."""
    # Pull inquiries from XCom
    inquiries = context['task_instance'].xcom_pull(
        task_ids='load_unprocessed_inquiries',
        key='inquiries'
    )
    
    if not inquiries:
        print("No inquiries to classify")
        return 0
    
    # Initialize real models
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
        
        # Classify using real BERT models
        category, cat_conf, cat_scores = classifier.predict(combined_text, include_all_scores=True)
        sentiment, sent_conf, sent_scores = sentiment_analyzer.predict(combined_text, include_all_scores=True)
        urgency, urg_conf, urg_scores = urgency_detector.predict(combined_text, include_all_scores=True)
        
        predictions.append({
            'inquiry_id': inquiry['id'],
            'category': category,
            'category_confidence': cat_conf,
            'sentiment': sentiment,
            'sentiment_confidence': sent_conf,
            'urgency': urgency,
            'urgency_confidence': urg_conf,
            'all_scores': {
                'category_scores': cat_scores,
                'sentiment_scores': sent_scores,
                'urgency_scores': urg_scores
            }
        })
    
    print(f"Classified {len(predictions)} inquiries using BERT models")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='predictions', value=predictions)
    return len(predictions)


def route_inquiries(**context):
    """Route inquiries using real routing logic."""
    # Pull predictions from XCom
    predictions = context['task_instance'].xcom_pull(
        task_ids='classify_inquiries',
        key='predictions'
    )
    
    if not predictions:
        print("No predictions to route")
        return 0
    
    # Load routing configuration
    routing_config = load_routing_config()
    
    # Initialize routing engine
    routing_engine = RoutingEngine()
    
    routing_decisions = []
    
    for pred in predictions:
        # Create prediction result object using proper enums
        prediction_result = PredictionResult(
            inquiry_id=pred['inquiry_id'],
            category=getattr(InquiryCategory, pred['category'].upper()),
            category_confidence=pred['category_confidence'],
            sentiment=getattr(SentimentType, pred['sentiment'].upper()),
            sentiment_confidence=pred['sentiment_confidence'],
            urgency=getattr(UrgencyLevel, pred['urgency'].upper()),
            urgency_confidence=pred['urgency_confidence'],
            model_versions={'classifier': 'bert-v1.0', 'sentiment': 'roberta-v1.0', 'urgency': 'bert-v1.0'},
        )
        
        # Route using real routing engine
        routing = routing_engine.route(pred['inquiry_id'], prediction_result)
        
        routing_decisions.append({
            'inquiry_id': pred['inquiry_id'],
            'department': routing.department.value,
            'assigned_consultant': routing.assigned_consultant,
            'priority_score': routing.priority_score,
            'escalated': routing.escalated,
            'routing_reason': routing.routing_reason,
        })
    
    print(f"Routed {len(routing_decisions)} inquiries using real routing logic")
    
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
            '{"classifier": "facebook/bart-large-mnli", "sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest", "urgency": "bert-urgency-v1.0"}',
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
    execution_timeout=timedelta(minutes=30),  # Specific timeout for ML task (BERT model downloads)
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

