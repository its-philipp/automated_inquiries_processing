"""
Airflow DAG for daily data ingestion from various sources.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import sys
import json
from pathlib import Path
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'daily_data_ingestion',
    default_args=default_args,
    description='Daily ingestion of new inquiries from data sources',
    schedule_interval='@daily',
    catchup=False,
    tags=['ingestion', 'etl'],
)


def fetch_new_inquiries(**context):
    """
    Generate new mock inquiries for demo purposes.
    
    In production, this would fetch from:
    - Email server (IMAP)
    - S3 bucket
    - API endpoint
    - Message queue
    
    For demo, we'll generate new mock data.
    """
    from faker import Faker
    import random
    from datetime import datetime, timedelta
    
    fake = Faker()
    
    # Generate 10-20 new inquiries
    num_inquiries = random.randint(10, 20)
    inquiries = []
    
    subjects = [
        "Technical issue with login",
        "Billing question about charges",
        "Feature request for mobile app",
        "Account access problem",
        "Payment method update",
        "Product feedback",
        "HR inquiry about benefits",
        "Legal question about terms",
        "Sales inquiry about enterprise plan",
        "Support ticket escalation"
    ]
    
    bodies = [
        "I'm having trouble logging into my account. The system keeps showing an error message.",
        "I noticed some unexpected charges on my recent bill. Can you help me understand what these are for?",
        "I would love to see a dark mode feature in the mobile app. Any plans for this?",
        "I can't access my account after the recent password reset. The new password isn't working.",
        "I need to update my payment method. How do I change my credit card information?",
        "The new dashboard design is great! However, I'd like to see more customization options.",
        "I have questions about my health insurance benefits. Can someone from HR help me?",
        "I need clarification on the terms of service regarding data retention policies.",
        "Our company is interested in the enterprise plan. Can we schedule a demo?",
        "My previous support ticket wasn't resolved. I need this escalated to a senior technician."
    ]
    
    categories = ["technical_support", "billing", "sales", "hr", "legal", "product_feedback"]
    
    for i in range(num_inquiries):
        # Generate timestamp within last 24 hours
        timestamp = datetime.now() - timedelta(
            hours=random.randint(0, 24),
            minutes=random.randint(0, 59)
        )
        
        inquiry = {
            "id": str(uuid.uuid4()),
            "subject": random.choice(subjects),
            "body": random.choice(bodies),
            "sender_email": fake.email(),
            "timestamp": timestamp.isoformat(),
            "source": random.choice(["email", "web_form", "api", "chat"]),
            "priority": random.choice(["low", "medium", "high"]),
            "category": random.choice(categories),
            "metadata": {
                "user_agent": fake.user_agent(),
                "ip_address": fake.ipv4(),
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                "device": random.choice(["desktop", "mobile", "tablet"])
            }
        }
        inquiries.append(inquiry)
    
    print(f"Generated {len(inquiries)} new mock inquiries")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='new_inquiries', value=inquiries)
    return len(inquiries)


def validate_data_quality(**context):
    """Validate data quality of fetched inquiries."""
    inquiries = context['task_instance'].xcom_pull(
        task_ids='fetch_new_inquiries',
        key='new_inquiries'
    )
    
    if not inquiries:
        print("No inquiries to validate")
        return True
    
    valid_inquiries = []
    invalid_count = 0
    
    for inquiry in inquiries:
        # Check required fields
        if not inquiry.get('subject') or not inquiry.get('body'):
            invalid_count += 1
            continue
        
        if not inquiry.get('sender_email'):
            invalid_count += 1
            continue
        
        # Check lengths
        if len(inquiry['subject']) > 500 or len(inquiry['body']) > 10000:
            invalid_count += 1
            continue
        
        valid_inquiries.append(inquiry)
    
    print(f"Validated {len(valid_inquiries)} inquiries, {invalid_count} invalid")
    
    # Push valid inquiries to XCom
    context['task_instance'].xcom_push(key='valid_inquiries', value=valid_inquiries)
    
    return len(valid_inquiries)


def store_inquiries(**context):
    """Store validated inquiries in database."""
    import psycopg2
    
    inquiries = context['task_instance'].xcom_pull(
        task_ids='validate_data_quality',
        key='valid_inquiries'
    )
    
    if not inquiries:
        print("No inquiries to store")
        return 0
    
    # Direct database connection
    try:
        conn = psycopg2.connect(
            host='postgresql.inquiries-system.svc.cluster.local',
            port=5432,
            database='inquiry_automation',
            user='postgres',
            password='postgres'
        )
        cursor = conn.cursor()
        
        stored_count = 0
        
        for inquiry in inquiries:
            inquiry_id = str(uuid.uuid4())
            
            try:
                cursor.execute("""
                    INSERT INTO inquiries (
                        id, subject, body, sender_email, sender_name,
                        timestamp, meta_data, processed
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    inquiry_id,
                    inquiry['subject'],
                    inquiry['body'],
                    inquiry['sender_email'],
                    inquiry.get('sender_name'),
                    inquiry.get('timestamp', datetime.now()),
                    json.dumps(inquiry.get('metadata', {})),
                    False,
                ))
                stored_count += 1
            except Exception as e:
                print(f"Error storing inquiry: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Stored {stored_count} inquiries")
        return stored_count
        
    except Exception as e:
        print(f"Database connection error: {e}")
        return 0


def log_ingestion_stats(**context):
    """Log ingestion statistics."""
    fetched = context['task_instance'].xcom_pull(
        task_ids='fetch_new_inquiries',
        key='return_value'
    )
    validated = context['task_instance'].xcom_pull(
        task_ids='validate_data_quality',
        key='return_value'
    )
    stored = context['task_instance'].xcom_pull(
        task_ids='store_inquiries',
        key='return_value'
    )
    
    stats = {
        'date': datetime.now().isoformat(),
        'fetched': fetched,
        'validated': validated,
        'stored': stored,
        'validation_rate': f"{(validated/fetched*100):.1f}%" if fetched > 0 else "0%",
        'storage_rate': f"{(stored/validated*100):.1f}%" if validated > 0 else "0%",
    }
    
    print(f"Ingestion Stats: {json.dumps(stats, indent=2)}")
    
    return stats


# Define tasks
fetch_task = PythonOperator(
    task_id='fetch_new_inquiries',
    python_callable=fetch_new_inquiries,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

store_task = PythonOperator(
    task_id='store_inquiries',
    python_callable=store_inquiries,
    dag=dag,
)

log_task = PythonOperator(
    task_id='log_ingestion_stats',
    python_callable=log_ingestion_stats,
    dag=dag,
)

# Define task dependencies
fetch_task >> validate_task >> store_task >> log_task

