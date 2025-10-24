# terraform.tfvars
# Project Configuration
project_name = "inquiry-automation"
environment  = "dev"
namespace    = "inquiries-system"

# Kubernetes Cluster Configuration
# For local clusters (minikube, kind, k3s), leave these empty to use kubeconfig
cluster_endpoint = ""
cluster_ca_certificate = ""
cluster_token = ""

# Database Configuration
db_password = "postgres"
