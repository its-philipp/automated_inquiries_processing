#!/usr/bin/env python3
"""
Script to populate MLflow with BERT model tracking data and test the complete setup.
"""
import os
import sys
import time
import random
import mlflow
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def create_bert_model_experiments():
    """Create realistic BERT model experiments in MLflow."""
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri("http://localhost:5001")
    
    # Create BERT-specific experiments
    experiments = [
        "bert_classification",
        "roberta_sentiment", 
        "model_performance",
        "inference_metrics"
    ]
    
    for exp_name in experiments:
        try:
            exp_id = mlflow.create_experiment(exp_name)
            print(f"✅ Created experiment: {exp_name} (ID: {exp_id})")
        except mlflow.exceptions.MlflowException as e:
            if "already exists" in str(e):
                print(f"⚠️  Experiment {exp_name} already exists")
            else:
                print(f"❌ Error creating experiment {exp_name}: {e}")
    
    # Generate realistic BERT model runs
    random.seed(42)
    
    # Experiment 1: BERT Classification
    mlflow.set_experiment("bert_classification")
    
    # Simulate multiple model versions
    for version in range(1, 4):
        with mlflow.start_run(run_name=f"bert_classifier_v{version}"):
            # Log model parameters
            mlflow.log_param("model_type", "facebook/bart-large-mnli")
            mlflow.log_param("task", "zero_shot_classification")
            mlflow.log_param("max_length", 512)
            mlflow.log_param("batch_size", 16)
            mlflow.log_param("model_version", f"v{version}")
            
            # Log realistic metrics
            base_accuracy = 0.85 + (version - 1) * 0.02
            mlflow.log_metric("accuracy", base_accuracy + random.uniform(-0.01, 0.01))
            mlflow.log_metric("precision", base_accuracy + random.uniform(-0.02, 0.02))
            mlflow.log_metric("recall", base_accuracy + random.uniform(-0.02, 0.02))
            mlflow.log_metric("f1_score", base_accuracy + random.uniform(-0.01, 0.01))
            mlflow.log_metric("inference_time_ms", 150 + random.uniform(-20, 20))
            mlflow.log_metric("confidence_score", 0.88 + random.uniform(-0.05, 0.05))
            
            # Log tags
            mlflow.set_tag("model_family", "BERT")
            mlflow.set_tag("framework", "transformers")
            mlflow.set_tag("task", "classification")
            mlflow.set_tag("status", "production" if version == 3 else "staging")
            
            print(f"✅ Logged BERT classifier v{version}")
    
    # Experiment 2: RoBERTa Sentiment
    mlflow.set_experiment("roberta_sentiment")
    
    for version in range(1, 3):
        with mlflow.start_run(run_name=f"roberta_sentiment_v{version}"):
            mlflow.log_param("model_type", "cardiffnlp/twitter-roberta-base-sentiment-latest")
            mlflow.log_param("task", "sentiment_analysis")
            mlflow.log_param("max_length", 128)
            mlflow.log_param("model_version", f"v{version}")
            
            base_accuracy = 0.92 + (version - 1) * 0.01
            mlflow.log_metric("accuracy", base_accuracy + random.uniform(-0.01, 0.01))
            mlflow.log_metric("precision", base_accuracy + random.uniform(-0.02, 0.02))
            mlflow.log_metric("recall", base_accuracy + random.uniform(-0.02, 0.02))
            mlflow.log_metric("f1_score", base_accuracy + random.uniform(-0.01, 0.01))
            mlflow.log_metric("inference_time_ms", 80 + random.uniform(-10, 10))
            mlflow.log_metric("confidence_score", 0.91 + random.uniform(-0.03, 0.03))
            
            mlflow.set_tag("model_family", "RoBERTa")
            mlflow.set_tag("framework", "transformers")
            mlflow.set_tag("task", "sentiment")
            mlflow.set_tag("status", "production" if version == 2 else "staging")
            
            print(f"✅ Logged RoBERTa sentiment v{version}")
    
    # Experiment 3: Model Performance Over Time
    mlflow.set_experiment("model_performance")
    
    # Simulate performance over time
    base_time = datetime.now() - timedelta(hours=24)
    for hour in range(0, 24, 2):
        with mlflow.start_run(run_name=f"performance_hour_{hour}"):
            timestamp = base_time + timedelta(hours=hour)
            mlflow.log_param("timestamp", timestamp.isoformat())
            mlflow.log_param("hour", hour)
            
            # Simulate varying performance
            requests = 100 + random.randint(-20, 50)
            avg_confidence = 0.85 + random.uniform(-0.05, 0.05)
            avg_inference_time = 120 + random.uniform(-30, 30)
            error_rate = 0.01 + random.uniform(0, 0.02)
            
            mlflow.log_metric("requests_per_hour", requests)
            mlflow.log_metric("avg_confidence", avg_confidence)
            mlflow.log_metric("avg_inference_time_ms", avg_inference_time)
            mlflow.log_metric("error_rate", error_rate)
            mlflow.log_metric("success_rate", 1 - error_rate)
            
            mlflow.set_tag("period", "hourly")
            mlflow.set_tag("data_type", "performance")
            
            print(f"✅ Logged performance data for hour {hour}")
    
    # Experiment 4: Inference Metrics
    mlflow.set_experiment("inference_metrics")
    
    # Simulate detailed inference metrics
    categories = ["technical_support", "billing", "sales", "hr", "legal", "product_feedback"]
    sentiments = ["positive", "negative", "neutral"]
    
    for category in categories:
        with mlflow.start_run(run_name=f"inference_{category}"):
            mlflow.log_param("category", category)
            mlflow.log_param("model_type", "bert_classifier")
            
            # Category-specific metrics
            mlflow.log_metric("prediction_count", random.randint(50, 200))
            mlflow.log_metric("avg_confidence", 0.82 + random.uniform(-0.05, 0.05))
            mlflow.log_metric("avg_inference_time_ms", 140 + random.uniform(-20, 20))
            mlflow.log_metric("accuracy", 0.87 + random.uniform(-0.03, 0.03))
            
            mlflow.set_tag("category", category)
            mlflow.set_tag("metric_type", "inference")
            
            print(f"✅ Logged inference metrics for {category}")
    
    for sentiment in sentiments:
        with mlflow.start_run(run_name=f"sentiment_{sentiment}"):
            mlflow.log_param("sentiment", sentiment)
            mlflow.log_param("model_type", "roberta_sentiment")
            
            mlflow.log_metric("prediction_count", random.randint(30, 150))
            mlflow.log_metric("avg_confidence", 0.89 + random.uniform(-0.04, 0.04))
            mlflow.log_metric("avg_inference_time_ms", 75 + random.uniform(-15, 15))
            mlflow.log_metric("accuracy", 0.91 + random.uniform(-0.02, 0.02))
            
            mlflow.set_tag("sentiment", sentiment)
            mlflow.set_tag("metric_type", "sentiment")
            
            print(f"✅ Logged sentiment metrics for {sentiment}")
    
    print("\n🎉 BERT model tracking setup complete!")
    print("📊 You can now view experiments at: http://localhost:5001")
    print("🔍 Try these URLs:")
    print("  - All experiments: http://localhost:5001/#/experiments")
    print("  - BERT Classification: http://localhost:5001/#/experiments/bert_classification")
    print("  - RoBERTa Sentiment: http://localhost:5001/#/experiments/roberta_sentiment")
    print("  - Model Performance: http://localhost:5001/#/experiments/model_performance")
    print("  - Inference Metrics: http://localhost:5001/#/experiments/inference_metrics")

if __name__ == "__main__":
    create_bert_model_experiments()
