"""
Airflow DAG for batch classification of inquiries (Simplified version).
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import psycopg2

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(minutes=30),
}

dag = DAG(
    'batch_classify_inquiries',
    default_args=default_args,
    description='Batch classification and routing of unprocessed inquiries',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['ml', 'classification', 'batch'],
)


def load_unprocessed_inquiries(**context):
    """Load unprocessed inquiries from database."""
    conn = psycopg2.connect(
        host='postgresql.inquiries-system.svc.cluster.local',
        port=5432,
        database='inquiry_automation',
        user='postgres',
        password='postgres'
    )
    cursor = conn.cursor()
    
    # For rule-based: no limit needed (can handle thousands)
    # For BERT: limit to 50 to avoid OOM
    import os
    use_rule_based = os.getenv('USE_RULE_BASED_CLASSIFICATION', 'false').lower() == 'true'
    limit_clause = "" if use_rule_based else "LIMIT 50"
    
    query = f"""
        SELECT id, subject, body, sender_email, sender_name, timestamp
        FROM inquiries
        WHERE processed = FALSE
        {limit_clause}
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
    context['task_instance'].xcom_push(key='inquiries', value=inquiries)
    return len(inquiries)


def classify_inquiries(**context):
    """Classify inquiries using BERT models (with rule-based fallback)."""
    inquiries = context['task_instance'].xcom_pull(
        task_ids='load_unprocessed_inquiries',
        key='inquiries'
    )
    
    if not inquiries:
        print("No inquiries to classify")
        return 0
    
    # Check if we should use BERT based on environment
    import os
    force_rule_based = os.getenv('USE_RULE_BASED_CLASSIFICATION', 'false').lower() == 'true'
    
    # Try to use BERT models (only if not forced to use rule-based)
    use_bert = False
    if not force_rule_based:
        try:
            print("⏳ Attempting to load BERT models...")
            from transformers import pipeline
            classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
            use_bert = True
            print("✅ Using BERT models for classification")
        except Exception as e:
            print(f"⚠️  BERT models not available ({e}), falling back to rule-based classification")
            use_bert = False
    else:
        print("⚠️  System memory <16GB - Using fast rule-based classification instead of BERT")
    
    predictions = []
    
    if use_bert:
        # BERT-based classification
        categories = ["technical_support", "billing", "sales", "hr", "legal", "product_feedback"]
        
        for inquiry in inquiries:
            text = f"{inquiry.get('subject', '')} {inquiry.get('body', '')}"
            
            # Category classification
            cat_result = classifier(text, candidate_labels=categories)
            category = cat_result['labels'][0]
            category_confidence = cat_result['scores'][0]
            
            # Sentiment classification
            sent_result = sentiment_analyzer(text[:512])  # Truncate to max length
            sentiment = sent_result[0]['label'].lower()
            sentiment_confidence = sent_result[0]['score']
            
            # Urgency classification (rule-based for now)
            text_lower = text.lower()
            if any(word in text_lower for word in ['urgent', 'asap', 'emergency', 'critical']):
                urgency = 'critical'
                urgency_confidence = 0.90
            elif any(word in text_lower for word in ['important', 'soon', 'priority']):
                urgency = 'high'
                urgency_confidence = 0.80
            else:
                urgency = 'medium'
                urgency_confidence = 0.70
            
            predictions.append({
                'inquiry_id': inquiry['id'],
                'category': category,
                'category_confidence': float(category_confidence),
                'sentiment': sentiment,
                'sentiment_confidence': float(sentiment_confidence),
                'urgency': urgency,
                'urgency_confidence': urgency_confidence,
            })
    else:
        # Rule-based fallback classification
        for inquiry in inquiries:
            text = f"{inquiry.get('subject', '')} {inquiry.get('body', '')}".lower()
        
            # Category classification
            if any(word in text for word in ['billing', 'charge', 'payment', 'invoice']):
                category = 'billing'
                category_confidence = 0.85
            elif any(word in text for word in ['technical', 'error', 'bug', 'not working', 'login']):
                category = 'technical_support'
                category_confidence = 0.85
            elif any(word in text for word in ['sales', 'pricing', 'demo', 'enterprise']):
                category = 'sales'
                category_confidence = 0.85
            elif any(word in text for word in ['hr', 'benefits', 'leave', 'policy']):
                category = 'hr'
                category_confidence = 0.85
            elif any(word in text for word in ['legal', 'terms', 'privacy', 'compliance']):
                category = 'legal'
                category_confidence = 0.85
            else:
                category = 'product_feedback'
                category_confidence = 0.60
            
            # Sentiment classification
            if any(word in text for word in ['love', 'great', 'excellent', 'wonderful', 'thank']):
                sentiment = 'positive'
                sentiment_confidence = 0.80
            elif any(word in text for word in ['hate', 'terrible', 'awful', 'worst', 'angry']):
                sentiment = 'negative'
                sentiment_confidence = 0.80
            else:
                sentiment = 'neutral'
                sentiment_confidence = 0.75
            
            # Urgency classification
            if any(word in text for word in ['urgent', 'asap', 'emergency', 'critical', 'immediately']):
                urgency = 'critical'
                urgency_confidence = 0.90
            elif any(word in text for word in ['important', 'soon', 'priority']):
                urgency = 'high'
                urgency_confidence = 0.80
            else:
                urgency = 'medium'
                urgency_confidence = 0.70
            
            predictions.append({
                'inquiry_id': inquiry['id'],
                'category': category,
                'category_confidence': category_confidence,
                'sentiment': sentiment,
                'sentiment_confidence': sentiment_confidence,
                'urgency': urgency,
                'urgency_confidence': urgency_confidence,
            })
    
    method = "BERT models" if use_bert else "rule-based logic"
    print(f"Classified {len(predictions)} inquiries using {method}")
    context['task_instance'].xcom_push(key='predictions', value=predictions)
    return len(predictions)


def route_inquiries(**context):
    """Route inquiries based on category."""
    predictions = context['task_instance'].xcom_pull(
        task_ids='classify_inquiries',
        key='predictions'
    )
    
    if not predictions:
        print("No predictions to route")
        return 0
    
    routing_decisions = []
    
    # Simple department routing
    department_map = {
        'billing': 'billing',
        'technical_support': 'support',
        'sales': 'sales',
        'hr': 'hr',
        'legal': 'legal',
        'product_feedback': 'product'
    }
    
    for pred in predictions:
        department = department_map.get(pred['category'], 'general')
        
        # Calculate priority score
        urgency_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        priority_score = urgency_scores.get(pred['urgency'], 2) * 10
        
        # Check if needs escalation
        escalated = pred['urgency'] == 'critical' or pred['category_confidence'] < 0.70
        
        routing_decisions.append({
            'inquiry_id': pred['inquiry_id'],
            'department': department,
            'assigned_consultant': f"{department}_team",
            'priority_score': priority_score,
            'escalated': escalated,
            'routing_reason': f"Classified as {pred['category']} with {pred['category_confidence']:.0%} confidence",
        })
    
    print(f"Routed {len(routing_decisions)} inquiries")
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
    
    conn = psycopg2.connect(
        host='postgresql.inquiries-system.svc.cluster.local',
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
            '{"classifier": "rule-based-v1.0", "sentiment": "rule-based-v1.0", "urgency": "rule-based-v1.0"}',
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

