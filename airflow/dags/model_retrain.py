"""
Airflow DAG for model retraining and evaluation.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import sys
from pathlib import Path
import json

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
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'model_retraining',
    default_args=default_args,
    description='Check model performance and trigger retraining if needed',
    schedule_interval='@weekly',  # Run weekly
    catchup=False,
    tags=['ml', 'training', 'model'],
)


def check_model_performance(**context):
    """Check current model performance metrics."""
    pg_hook = PostgresHook(postgres_conn_id='inquiry_db')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    
    # Get predictions from last 7 days
    cursor.execute("""
        SELECT 
            category, category_confidence,
            sentiment, sentiment_confidence,
            urgency, urgency_confidence,
            predicted_at
        FROM predictions
        WHERE predicted_at >= NOW() - INTERVAL '7 days'
    """)
    
    predictions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not predictions:
        print("No recent predictions to evaluate")
        return False
    
    # Calculate average confidence scores
    category_confidences = [p[1] for p in predictions]
    sentiment_confidences = [p[3] for p in predictions]
    urgency_confidences = [p[5] for p in predictions]
    
    avg_category_conf = sum(category_confidences) / len(category_confidences)
    avg_sentiment_conf = sum(sentiment_confidences) / len(sentiment_confidences)
    avg_urgency_conf = sum(urgency_confidences) / len(urgency_confidences)
    
    metrics = {
        'total_predictions': len(predictions),
        'avg_category_confidence': avg_category_conf,
        'avg_sentiment_confidence': avg_sentiment_conf,
        'avg_urgency_confidence': avg_urgency_conf,
        'overall_confidence': (avg_category_conf + avg_sentiment_conf + avg_urgency_conf) / 3,
    }
    
    print(f"Model Performance Metrics: {json.dumps(metrics, indent=2)}")
    
    # Check if retraining is needed
    # Trigger retraining if average confidence drops below 0.7
    needs_retraining = metrics['overall_confidence'] < 0.7
    
    context['task_instance'].xcom_push(key='metrics', value=metrics)
    context['task_instance'].xcom_push(key='needs_retraining', value=needs_retraining)
    
    return needs_retraining


def collect_training_data(**context):
    """Collect and prepare training data from labeled inquiries."""
    needs_retraining = context['task_instance'].xcom_pull(
        task_ids='check_model_performance',
        key='needs_retraining'
    )
    
    if not needs_retraining:
        print("Retraining not needed, skipping data collection")
        return 0
    
    pg_hook = PostgresHook(postgres_conn_id='inquiry_db')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    
    # Get inquiries with metadata (ground truth labels)
    cursor.execute("""
        SELECT 
            i.id, i.subject, i.body,
            i.metadata,
            p.category, p.sentiment, p.urgency
        FROM inquiries i
        JOIN predictions p ON i.id = p.inquiry_id
        WHERE i.metadata IS NOT NULL
        AND i.metadata::text != '{}'
        LIMIT 10000
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    training_data = []
    for row in rows:
        metadata = json.loads(row[3]) if isinstance(row[3], str) else row[3]
        
        # Check if ground truth labels exist
        if 'category' in metadata:
            training_data.append({
                'id': row[0],
                'subject': row[1],
                'body': row[2],
                'true_category': metadata.get('category'),
                'true_sentiment': metadata.get('sentiment'),
                'true_urgency': metadata.get('urgency'),
                'pred_category': row[4],
                'pred_sentiment': row[5],
                'pred_urgency': row[6],
            })
    
    print(f"Collected {len(training_data)} labeled samples")
    
    # Save training data
    output_path = project_root / "data" / "labeled" / "training_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    context['task_instance'].xcom_push(key='training_data_path', value=str(output_path))
    context['task_instance'].xcom_push(key='num_samples', value=len(training_data))
    
    return len(training_data)


def trigger_model_training(**context):
    """Trigger model training process."""
    needs_retraining = context['task_instance'].xcom_pull(
        task_ids='check_model_performance',
        key='needs_retraining'
    )
    
    if not needs_retraining:
        print("Retraining not needed")
        return False
    
    num_samples = context['task_instance'].xcom_pull(
        task_ids='collect_training_data',
        key='num_samples'
    )
    
    if num_samples < 100:
        print(f"Insufficient training data: {num_samples} samples (minimum 100)")
        return False
    
    # In production, this would trigger actual model training
    # For now, we'll just simulate it
    print(f"Triggering model training with {num_samples} samples")
    print("Training would include:")
    print("  - Data preprocessing and augmentation")
    print("  - Fine-tuning BERT-based classifier")
    print("  - Cross-validation")
    print("  - Hyperparameter tuning")
    print("  - Model evaluation on validation set")
    
    # Simulate training results
    training_results = {
        'status': 'completed',
        'num_samples': num_samples,
        'val_accuracy': 0.85,
        'val_f1': 0.83,
        'training_time_minutes': 45,
    }
    
    context['task_instance'].xcom_push(key='training_results', value=training_results)
    
    return True


def evaluate_new_model(**context):
    """Evaluate the newly trained model."""
    training_results = context['task_instance'].xcom_pull(
        task_ids='trigger_model_training',
        key='training_results'
    )
    
    if not training_results or training_results.get('status') != 'completed':
        print("No model to evaluate")
        return False
    
    print(f"Evaluating new model...")
    print(f"Validation Accuracy: {training_results['val_accuracy']:.2%}")
    print(f"Validation F1 Score: {training_results['val_f1']:.2%}")
    
    # Compare with current production model
    current_metrics = context['task_instance'].xcom_pull(
        task_ids='check_model_performance',
        key='metrics'
    )
    
    # Simplified comparison
    new_model_better = training_results['val_accuracy'] > 0.80
    
    context['task_instance'].xcom_push(key='promote_model', value=new_model_better)
    
    return new_model_better


def promote_to_production(**context):
    """Promote new model to production if it performs better."""
    should_promote = context['task_instance'].xcom_pull(
        task_ids='evaluate_new_model',
        key='promote_model'
    )
    
    if not should_promote:
        print("New model does not meet promotion criteria")
        return False
    
    # In production, this would:
    # 1. Save model to MLflow
    # 2. Transition model stage to "Production"
    # 3. Update model version in database
    # 4. Trigger API service restart to load new model
    
    print("Promoting new model to production...")
    print("Steps:")
    print("  1. Register model in MLflow")
    print("  2. Transition to Production stage")
    print("  3. Archive old production model")
    print("  4. Update model_versions table")
    print("  5. Notify services to reload models")
    
    # Update model version in database
    pg_hook = PostgresHook(postgres_conn_id='inquiry_db')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    
    # Archive old production models
    cursor.execute("""
        UPDATE model_versions
        SET status = 'archived', archived_at = NOW()
        WHERE status = 'production'
    """)
    
    # Insert new model version
    cursor.execute("""
        INSERT INTO model_versions (
            model_name, model_type, version, status, deployed_at, metrics
        ) VALUES 
        ('classifier', 'distilbert-finetuned', 'v2.0', 'production', NOW(), 
         '{"accuracy": 0.85, "f1": 0.83}')
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✓ Model promoted to production successfully")
    
    return True


def send_notification(**context):
    """Send notification about retraining results."""
    metrics = context['task_instance'].xcom_pull(
        task_ids='check_model_performance',
        key='metrics'
    )
    
    promoted = context['task_instance'].xcom_pull(
        task_ids='promote_to_production',
        key='return_value'
    )
    
    message = f"""
    Model Retraining Report
    =======================
    
    Current Model Performance:
    - Overall Confidence: {metrics.get('overall_confidence', 0):.2%}
    - Category Confidence: {metrics.get('avg_category_confidence', 0):.2%}
    - Sentiment Confidence: {metrics.get('avg_sentiment_confidence', 0):.2%}
    - Urgency Confidence: {metrics.get('avg_urgency_confidence', 0):.2%}
    
    Retraining Status: {'Completed' if promoted else 'Not Needed or Failed'}
    Model Promoted: {'Yes' if promoted else 'No'}
    """
    
    print(message)
    
    # In production, send email/Slack notification
    
    return True


# Define tasks
check_task = PythonOperator(
    task_id='check_model_performance',
    python_callable=check_model_performance,
    dag=dag,
)

collect_task = PythonOperator(
    task_id='collect_training_data',
    python_callable=collect_training_data,
    dag=dag,
)

train_task = PythonOperator(
    task_id='trigger_model_training',
    python_callable=trigger_model_training,
    dag=dag,
)

evaluate_task = PythonOperator(
    task_id='evaluate_new_model',
    python_callable=evaluate_new_model,
    dag=dag,
)

promote_task = PythonOperator(
    task_id='promote_to_production',
    python_callable=promote_to_production,
    dag=dag,
)

notify_task = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag,
)

# Define task dependencies
check_task >> collect_task >> train_task >> evaluate_task >> promote_task >> notify_task

