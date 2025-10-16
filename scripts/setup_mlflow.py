#!/usr/bin/env python3
"""
Script to set up MLflow with sample experiments and models.
"""
import mlflow
import mlflow.sklearn
import mlflow.pytorch
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os

def create_sample_experiments():
    """Create sample experiments in MLflow."""
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri("http://localhost:5001")
    
    # Create experiments
    experiments = [
        "inquiry_classification",
        "sentiment_analysis", 
        "urgency_detection",
        "model_comparison"
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
    
    # Generate sample data for experiments
    np.random.seed(42)
    n_samples = 1000
    n_features = 20
    
    X = np.random.randn(n_samples, n_features)
    y_classification = np.random.choice(["technical_support", "billing", "sales", "hr"], n_samples)
    y_sentiment = np.random.choice(["positive", "neutral", "negative"], n_samples)
    y_urgency = np.random.choice(["low", "medium", "high", "critical"], n_samples)
    
    # Split data
    X_train, X_test, y_train_class, y_test_class = train_test_split(X, y_classification, test_size=0.2, random_state=42)
    _, _, y_train_sent, y_test_sent = train_test_split(X, y_sentiment, test_size=0.2, random_state=42)
    _, _, y_train_urg, y_test_urg = train_test_split(X, y_urgency, test_size=0.2, random_state=42)
    
    # Experiment 1: Inquiry Classification
    mlflow.set_experiment("inquiry_classification")
    
    with mlflow.start_run(run_name="rf_classifier_v1"):
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train_class)
        
        # Predictions
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test_class, y_pred)
        
        # Log parameters
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", None)
        mlflow.log_param("random_state", 42)
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("training_samples", len(X_train))
        mlflow.log_metric("test_samples", len(X_test))
        
        # Log model
        mlflow.sklearn.log_model(model, "model")
        
        print(f"✅ Logged classification model with accuracy: {accuracy:.3f}")
    
    # Experiment 2: Sentiment Analysis
    mlflow.set_experiment("sentiment_analysis")
    
    with mlflow.start_run(run_name="sentiment_rf_v1"):
        model = RandomForestClassifier(n_estimators=150, random_state=42)
        model.fit(X_train, y_train_sent)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test_sent, y_pred)
        
        mlflow.log_param("n_estimators", 150)
        mlflow.log_param("task", "sentiment_analysis")
        mlflow.log_metric("accuracy", accuracy)
        
        mlflow.sklearn.log_model(model, "sentiment_model")
        
        print(f"✅ Logged sentiment model with accuracy: {accuracy:.3f}")
    
    # Experiment 3: Urgency Detection
    mlflow.set_experiment("urgency_detection")
    
    with mlflow.start_run(run_name="urgency_rf_v1"):
        model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
        model.fit(X_train, y_train_urg)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test_urg, y_pred)
        
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("task", "urgency_detection")
        mlflow.log_metric("accuracy", accuracy)
        
        mlflow.sklearn.log_model(model, "urgency_model")
        
        print(f"✅ Logged urgency model with accuracy: {accuracy:.3f}")
    
    # Experiment 4: Model Comparison
    mlflow.set_experiment("model_comparison")
    
    models = [
        ("RandomForest", RandomForestClassifier(n_estimators=100, random_state=42)),
        ("RandomForest_Deep", RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)),
        ("RandomForest_Wide", RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42))
    ]
    
    for model_name, model in models:
        with mlflow.start_run(run_name=f"{model_name.lower()}_comparison"):
            model.fit(X_train, y_train_class)
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test_class, y_pred)
            
            mlflow.log_param("model_type", model_name)
            mlflow.log_param("n_estimators", model.n_estimators)
            mlflow.log_param("max_depth", model.max_depth)
            mlflow.log_metric("accuracy", accuracy)
            
            mlflow.sklearn.log_model(model, "model")
            
            print(f"✅ Logged {model_name} model with accuracy: {accuracy:.3f}")
    
    print("\n🎉 MLflow setup complete!")
    print("📊 You can now view experiments at: http://localhost:5001")

if __name__ == "__main__":
    create_sample_experiments()