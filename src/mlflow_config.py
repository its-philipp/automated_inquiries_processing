"""
MLflow configuration and utilities for model tracking and versioning.
"""
import os
from typing import Optional, Dict, Any
import mlflow
from mlflow.tracking import MlflowClient
from pathlib import Path


class MLflowConfig:
    """MLflow tracking and model registry configuration."""
    
    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: str = "inquiry-classification",
        artifact_location: Optional[str] = None,
    ):
        """
        Initialize MLflow configuration.
        
        Args:
            tracking_uri: MLflow tracking server URI
            experiment_name: Name of the MLflow experiment
            artifact_location: Location to store artifacts
        """
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI",
            "http://localhost:5000"
        )
        self.experiment_name = experiment_name
        self.artifact_location = artifact_location or os.getenv(
            "MLFLOW_ARTIFACT_ROOT",
            "./mlartifacts"
        )
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Create or get experiment
        self.experiment_id = self._get_or_create_experiment()
        
        # Initialize client
        self.client = MlflowClient(tracking_uri=self.tracking_uri)
    
    def _get_or_create_experiment(self) -> str:
        """Get or create MLflow experiment."""
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                self.experiment_name,
                artifact_location=self.artifact_location,
            )
        else:
            experiment_id = experiment.experiment_id
        return experiment_id
    
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """
        Start a new MLflow run.
        
        Args:
            run_name: Name for the run
            tags: Tags to attach to the run
            
        Returns:
            MLflow run context manager
        """
        return mlflow.start_run(
            experiment_id=self.experiment_id,
            run_name=run_name,
            tags=tags or {},
        )
    
    def log_model_metrics(
        self,
        metrics: Dict[str, float],
        step: Optional[int] = None,
    ):
        """
        Log metrics for current run.
        
        Args:
            metrics: Dictionary of metric names and values
            step: Optional step number
        """
        for name, value in metrics.items():
            mlflow.log_metric(name, value, step=step)
    
    def log_model_params(self, params: Dict[str, Any]):
        """
        Log parameters for current run.
        
        Args:
            params: Dictionary of parameter names and values
        """
        for name, value in params.items():
            mlflow.log_param(name, value)
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """
        Log an artifact (file) for current run.
        
        Args:
            local_path: Path to local file
            artifact_path: Path within artifact store
        """
        mlflow.log_artifact(local_path, artifact_path)
    
    def register_model(
        self,
        model_uri: str,
        model_name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Register a model in the MLflow model registry.
        
        Args:
            model_uri: URI of the model to register
            model_name: Name for the registered model
            tags: Tags for the model version
            
        Returns:
            ModelVersion object
        """
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=model_name,
            tags=tags,
        )
        return model_version
    
    def get_model_version(
        self,
        model_name: str,
        version: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> str:
        """
        Get model URI for a specific version or stage.
        
        Args:
            model_name: Registered model name
            version: Specific version number (e.g., "1", "2")
            stage: Model stage ("Production", "Staging", "None")
            
        Returns:
            Model URI string
        """
        if version:
            return f"models:/{model_name}/{version}"
        elif stage:
            return f"models:/{model_name}/{stage}"
        else:
            return f"models:/{model_name}/latest"
    
    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str,
        archive_existing: bool = True,
    ):
        """
        Transition a model version to a new stage.
        
        Args:
            model_name: Registered model name
            version: Model version number
            stage: Target stage ("Production", "Staging", "Archived")
            archive_existing: Archive existing models in target stage
        """
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=archive_existing,
        )
    
    def get_latest_model_version(self, model_name: str, stage: Optional[str] = None):
        """
        Get the latest model version.
        
        Args:
            model_name: Registered model name
            stage: Filter by stage
            
        Returns:
            Latest model version object
        """
        versions = self.client.search_model_versions(f"name='{model_name}'")
        if not versions:
            return None
        
        if stage:
            versions = [v for v in versions if v.current_stage == stage]
        
        if not versions:
            return None
        
        # Sort by version number
        versions.sort(key=lambda x: int(x.version), reverse=True)
        return versions[0]
    
    def compare_models(
        self,
        model_name: str,
        version1: str,
        version2: str,
        metric_names: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Compare two model versions by their metrics.
        
        Args:
            model_name: Registered model name
            version1: First version to compare
            version2: Second version to compare
            metric_names: List of metric names to compare
            
        Returns:
            Dictionary with comparison results
        """
        v1 = self.client.get_model_version(model_name, version1)
        v2 = self.client.get_model_version(model_name, version2)
        
        # Get runs
        run1 = self.client.get_run(v1.run_id)
        run2 = self.client.get_run(v2.run_id)
        
        comparison = {
            "version1": {
                "version": version1,
                "created": v1.creation_timestamp,
                "stage": v1.current_stage,
                "metrics": run1.data.metrics,
            },
            "version2": {
                "version": version2,
                "created": v2.creation_timestamp,
                "stage": v2.current_stage,
                "metrics": run2.data.metrics,
            },
        }
        
        # Calculate differences for specified metrics
        if metric_names:
            differences = {}
            for metric in metric_names:
                val1 = run1.data.metrics.get(metric, 0)
                val2 = run2.data.metrics.get(metric, 0)
                differences[metric] = val2 - val1
            comparison["differences"] = differences
        
        return comparison


# Global MLflow config instance
_mlflow_config = None


def get_mlflow_config() -> MLflowConfig:
    """Get or create global MLflow config instance."""
    global _mlflow_config
    if _mlflow_config is None:
        _mlflow_config = MLflowConfig()
    return _mlflow_config


def init_mlflow(
    tracking_uri: Optional[str] = None,
    experiment_name: str = "inquiry-classification",
) -> MLflowConfig:
    """
    Initialize MLflow configuration.
    
    Args:
        tracking_uri: MLflow tracking server URI
        experiment_name: Experiment name
        
    Returns:
        MLflowConfig instance
    """
    global _mlflow_config
    _mlflow_config = MLflowConfig(
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
    )
    return _mlflow_config

