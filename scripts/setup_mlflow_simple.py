#!/usr/bin/env python3
"""
Simple script to set up MLflow with sample experiments and metrics.
"""
import mlflow
import numpy as np
import time

def create_simple_experiments():
    """Create sample experiments in MLflow with metrics only."""
    
    print("🚀 Starting MLflow setup...")
    print("📊 Setting MLflow tracking URI...")
    mlflow.set_tracking_uri("http://mlflow:5000")
    print("✅ MLflow tracking URI set to http://mlflow:5000")
    
    # Create experiments
    experiments = [
        "inquiry_classification",
        "sentiment_analysis", 
        "urgency_detection",
        "model_comparison"
    ]
    
    print(f"\n📁 Creating {len(experiments)} experiments...")
    for i, exp_name in enumerate(experiments, 1):
        print(f"🔄 [{i}/{len(experiments)}] Creating experiment: {exp_name}")
        try:
            exp_id = mlflow.create_experiment(exp_name)
            print(f"✅ Created experiment: {exp_name} (ID: {exp_id})")
        except mlflow.exceptions.MlflowException as e:
            if "already exists" in str(e):
                print(f"⚠️  Experiment {exp_name} already exists")
            else:
                print(f"❌ Error creating experiment {exp_name}: {e}")
        time.sleep(0.5)  # Small delay for better UX
    
    # Generate sample runs with metrics
    np.random.seed(42)
    
    # Experiment 1: Inquiry Classification
    mlflow.set_experiment("inquiry_classification")
    
    with mlflow.start_run(run_name="rf_classifier_v1"):
        mlflow.log_param("algorithm", "RandomForest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", None)
        mlflow.log_metric("accuracy", 0.847)
        mlflow.log_metric("precision", 0.832)
        mlflow.log_metric("recall", 0.847)
        mlflow.log_metric("f1_score", 0.839)
        mlflow.log_metric("training_time", 2.3)
        mlflow.set_tag("model_version", "v1.0")
        mlflow.set_tag("task", "classification")
        print("✅ Logged classification run")
    
    with mlflow.start_run(run_name="rf_classifier_v2"):
        mlflow.log_param("algorithm", "RandomForest")
        mlflow.log_param("n_estimators", 150)
        mlflow.log_param("max_depth", 10)
        mlflow.log_metric("accuracy", 0.856)
        mlflow.log_metric("precision", 0.841)
        mlflow.log_metric("recall", 0.856)
        mlflow.log_metric("f1_score", 0.848)
        mlflow.log_metric("training_time", 3.1)
        mlflow.set_tag("model_version", "v1.1")
        mlflow.set_tag("task", "classification")
        print("✅ Logged classification run v2")
    
    # Experiment 2: Sentiment Analysis
    mlflow.set_experiment("sentiment_analysis")
    
    with mlflow.start_run(run_name="sentiment_rf_v1"):
        mlflow.log_param("algorithm", "RandomForest")
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("task", "sentiment_analysis")
        mlflow.log_metric("accuracy", 0.723)
        mlflow.log_metric("precision", 0.715)
        mlflow.log_metric("recall", 0.723)
        mlflow.log_metric("f1_score", 0.719)
        mlflow.log_metric("training_time", 4.2)
        mlflow.set_tag("model_version", "v1.0")
        mlflow.set_tag("task", "sentiment")
        print("✅ Logged sentiment run")
    
    # Experiment 3: Urgency Detection
    mlflow.set_experiment("urgency_detection")
    
    with mlflow.start_run(run_name="urgency_rf_v1"):
        mlflow.log_param("algorithm", "RandomForest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 15)
        mlflow.log_param("task", "urgency_detection")
        mlflow.log_metric("accuracy", 0.891)
        mlflow.log_metric("precision", 0.883)
        mlflow.log_metric("recall", 0.891)
        mlflow.log_metric("f1_score", 0.887)
        mlflow.log_metric("training_time", 2.8)
        mlflow.set_tag("model_version", "v1.0")
        mlflow.set_tag("task", "urgency")
        print("✅ Logged urgency run")
    
    # Experiment 4: Model Comparison
    mlflow.set_experiment("model_comparison")
    
    models = [
        ("RandomForest", {"n_estimators": 100}, 0.847),
        ("RandomForest_Deep", {"n_estimators": 200, "max_depth": 15}, 0.856),
        ("RandomForest_Wide", {"n_estimators": 50, "max_depth": 5}, 0.823)
    ]
    
    for model_name, params, accuracy in models:
        with mlflow.start_run(run_name=f"{model_name.lower()}_comparison"):
            mlflow.log_param("model_type", model_name)
            for param_name, param_value in params.items():
                mlflow.log_param(param_name, param_value)
            
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", accuracy * 0.98)
            mlflow.log_metric("recall", accuracy * 1.02)
            mlflow.log_metric("f1_score", accuracy * 0.99)
            mlflow.log_metric("training_time", np.random.uniform(1.5, 5.0))
            
            mlflow.set_tag("comparison_run", True)
            mlflow.set_tag("model_type", model_name)
            
            print(f"✅ Logged {model_name} comparison run")
    
    print("\n🎉 MLflow setup complete!")
    print("📊 You can now view experiments at: http://localhost:5001")
    print("🔍 Try these URLs:")
    print("  - All experiments: http://localhost:5001/#/experiments")
    print("  - Classification: http://localhost:5001/#/experiments/1")
    print("  - Sentiment: http://localhost:5001/#/experiments/2")
    print("  - Urgency: http://localhost:5001/#/experiments/3")
    print("  - Comparison: http://localhost:5001/#/experiments/4")

if __name__ == "__main__":
    create_simple_experiments()
