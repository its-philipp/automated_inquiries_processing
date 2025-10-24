# Pure Kubernetes Infrastructure with CNCF Services
# This Terraform configuration deploys everything to an existing Kubernetes cluster
# No cloud provider required - works with any Kubernetes cluster (local, on-prem, cloud)

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

# Variables
variable "project_name" {
  description = "Project name"
  type        = string
  default     = "inquiry-automation"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "namespace" {
  description = "Kubernetes namespace for the application"
  type        = string
  default     = "inquiries-system"
}

variable "cluster_endpoint" {
  description = "Kubernetes cluster endpoint"
  type        = string
  default     = "https://kubernetes.default.svc"
}

variable "cluster_ca_certificate" {
  description = "Kubernetes cluster CA certificate"
  type        = string
  default     = ""
  sensitive   = true
}

variable "cluster_token" {
  description = "Kubernetes cluster token"
  type        = string
  default     = ""
  sensitive   = true
}

# Kubernetes Provider Configuration
provider "kubernetes" {
  host                   = var.cluster_endpoint
  cluster_ca_certificate = var.cluster_ca_certificate != "" ? base64decode(var.cluster_ca_certificate) : null
  token                  = var.cluster_token != "" ? var.cluster_token : null
  
  # For local clusters (minikube, kind, k3s)
  config_path = var.cluster_endpoint == "https://kubernetes.default.svc" ? null : "~/.kube/config"
}

provider "helm" {
  kubernetes {
    host                   = var.cluster_endpoint
    cluster_ca_certificate = var.cluster_ca_certificate != "" ? base64decode(var.cluster_ca_certificate) : null
    token                  = var.cluster_token != "" ? var.cluster_token : null
    
    config_path = var.cluster_endpoint == "https://kubernetes.default.svc" ? null : "~/.kube/config"
  }
}

# Namespaces
resource "kubernetes_namespace" "inquiries_system" {
  metadata {
    name = var.namespace
    labels = {
      "istio-injection" = "enabled"
      "environment"     = var.environment
    }
  }
}

resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
    labels = {
      "environment" = var.environment
    }
  }
}

resource "kubernetes_namespace" "istio_system" {
  metadata {
    name = "istio-system"
    labels = {
      "environment" = var.environment
    }
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      "environment" = var.environment
    }
  }
}

# Install Istio using Helm
resource "helm_release" "istio_base" {
  name       = "istio-base"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  version    = "1.19.0"
}

resource "helm_release" "istiod" {
  name       = "istiod"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  version    = "1.19.0"

  depends_on = [helm_release.istio_base]
}

resource "helm_release" "istio_ingressgateway" {
  name       = "istio-ingressgateway"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "gateway"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  version    = "1.19.0"

  values = [
    yamlencode({
      service = {
        type = "NodePort"
        ports = [
          {
            name = "http2"
            port = 80
            nodePort = 30080
          },
          {
            name = "https"
            port = 443
            nodePort = 30443
          }
        ]
      }
    })
  ]

  depends_on = [helm_release.istiod]
}

# Install ArgoCD using Helm
resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = kubernetes_namespace.argocd.metadata[0].name
  version    = "5.51.6"

  values = [
    yamlencode({
      server = {
        service = {
          type = "NodePort"
          ports = {
            server = {
              nodePort = 30009
            }
          }
        }
      }
      configs = {
        cm = {
          "application.instanceLabelKey" = "argocd.argoproj.io/instance"
        }
      }
    })
  ]
}

# Install Prometheus Stack using Helm
resource "helm_release" "prometheus_stack" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "55.0.0"

  values = [
    yamlencode({
      grafana = {
        enabled = true
        adminPassword = "admin"
        service = {
          type = "NodePort"
          ports = {
            service = {
              nodePort = 30001
            }
          }
        }
        persistence = {
          enabled = true
          size = "10Gi"
        }
      }
      prometheus = {
        prometheusSpec = {
          serviceMonitorSelectorNilUsesHelmValues = false
          podMonitorSelectorNilUsesHelmValues = false
          ruleSelectorNilUsesHelmValues = false
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                accessModes = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = "20Gi"
                  }
                }
              }
            }
          }
        }
        service = {
          type = "NodePort"
          ports = {
            web = {
              nodePort = 30002
            }
          }
        }
      }
      alertmanager = {
        enabled = true
        service = {
          type = "NodePort"
          ports = {
            web = {
              nodePort = 30003
            }
          }
        }
      }
    })
  ]
}

# Install Jaeger for distributed tracing
resource "helm_release" "jaeger" {
  name       = "jaeger"
  repository = "https://jaegertracing.github.io/helm-charts"
  chart      = "jaeger"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "0.71.0"

  values = [
    yamlencode({
      allInOne = {
        enabled = true
        image = {
          tag = "1.51"
        }
        service = {
          type = "NodePort"
          ports = {
            query = {
              nodePort = 30004
            }
          }
        }
      }
    })
  ]
}

# Install Fluentd for log aggregation
resource "helm_release" "fluentd" {
  name       = "fluentd"
  repository = "https://fluent.github.io/helm-charts"
  chart      = "fluentd"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "0.4.2"

  values = [
    yamlencode({
      service = {
        type = "NodePort"
        ports = {
          forward = {
            nodePort = 30005
          }
        }
      }
    })
  ]
}

# Application Secrets
resource "kubernetes_secret" "app_secrets" {
  metadata {
    name      = "app-secrets"
    namespace = kubernetes_namespace.inquiries_system.metadata[0].name
  }

  data = {
    database-url = "postgresql://postgres:postgres@postgresql:5432/inquiry_automation"
  }

  type = "Opaque"
}

# Deploy the application using Helm
resource "helm_release" "application" {
  name       = "automated-inquiries-processing"
  chart      = "../../k8s/helm"
  namespace  = kubernetes_namespace.inquiries_system.metadata[0].name

  values = [
    yamlencode({
      replicaCount = 2
      image = {
        repository = "python"
        tag = "3.11-slim"
        pullPolicy = "IfNotPresent"
      }
      service = {
        type = "ClusterIP"
        port = 8000
      }
      postgresql = {
        enabled = true
        auth = {
          postgresPassword = "postgres"
          database = "inquiry_automation"
        }
        primary = {
          persistence = {
            enabled = true
            size = "20Gi"
          }
          resources = {
            requests = {
              memory = "256Mi"
              cpu = "250m"
            }
            limits = {
              memory = "512Mi"
              cpu = "500m"
            }
          }
        }
      }
      redis = {
        enabled = true
        auth = {
          enabled = false
        }
        master = {
          persistence = {
            enabled = true
            size = "8Gi"
          }
          resources = {
            requests = {
              memory = "128Mi"
              cpu = "100m"
            }
            limits = {
              memory = "256Mi"
              cpu = "200m"
            }
          }
        }
      }
      mlflow = {
        enabled = true
        replicaCount = 1
        service = {
          type = "NodePort"
          port = 5000
          nodePort = 30006
        }
        resources = {
          requests = {
            memory = "512Mi"
            cpu = "250m"
          }
          limits = {
            memory = "1Gi"
            cpu = "500m"
          }
        }
        persistence = {
          enabled = true
          size = "10Gi"
        }
      }
      airflow = {
        enabled = true
        executor = "CeleryExecutor"
        webserver = {
          replicaCount = 1
          service = {
            type = "NodePort"
            port = 8080
            nodePort = 30007
          }
          resources = {
            requests = {
              memory = "512Mi"
              cpu = "250m"
            }
            limits = {
              memory = "1Gi"
              cpu = "500m"
            }
          }
        }
        scheduler = {
          replicaCount = 1
          resources = {
            requests = {
              memory = "512Mi"
              cpu = "250m"
            }
            limits = {
              memory = "1Gi"
              cpu = "500m"
            }
          }
        }
        workers = {
          replicaCount = 2
          resources = {
            requests = {
              memory = "1Gi"
              cpu = "500m"
            }
            limits = {
              memory = "2Gi"
              cpu = "1000m"
            }
          }
        }
      }
      istio = {
        enabled = true
        gateway = {
          enabled = true
          name = "inquiries-gateway"
          namespace = kubernetes_namespace.istio_system.metadata[0].name
        }
        virtualService = {
          enabled = true
          hosts = ["localhost"]
          gateways = ["${kubernetes_namespace.istio_system.metadata[0].name}/inquiries-gateway"]
          http = [{
            match = [{
              uri = {
                prefix = "/"
              }
            }]
            route = [{
              destination = {
                host = "automated-inquiries-processing"
                port = {
                  number = 8000
                }
              }
            }]
            timeout = "30s"
            retries = {
              attempts = 3
              perTryTimeout = "10s"
            }
          }]
        }
      }
    })
  ]

  depends_on = [
    kubernetes_secret.app_secrets,
    helm_release.istio_ingressgateway
  ]
}

# Apply Istio Gateway configuration
resource "kubernetes_manifest" "istio_gateway" {
  manifest = {
    apiVersion = "networking.istio.io/v1beta1"
    kind       = "Gateway"
    metadata = {
      name      = "inquiries-gateway"
      namespace = kubernetes_namespace.istio_system.metadata[0].name
    }
    spec = {
      selector = {
        istio = "ingressgateway"
      }
      servers = [
        {
          port = {
            number   = 80
            name     = "http"
            protocol = "HTTP"
          }
          hosts = ["localhost"]
        }
      ]
    }
  }

  depends_on = [helm_release.istio_ingressgateway]
}

# Apply Istio VirtualService configuration
resource "kubernetes_manifest" "istio_virtualservice" {
  manifest = {
    apiVersion = "networking.istio.io/v1beta1"
    kind       = "VirtualService"
    metadata = {
      name      = "inquiries-vs"
      namespace = kubernetes_namespace.inquiries_system.metadata[0].name
    }
    spec = {
      hosts    = ["localhost"]
      gateways = ["${kubernetes_namespace.istio_system.metadata[0].name}/inquiries-gateway"]
      http = [
        {
          match = [
            {
              uri = {
                prefix = "/"
              }
            }
          ]
          route = [
            {
              destination = {
                host = "automated-inquiries-processing"
                port = {
                  number = 8000
                }
              }
            }
          ]
          timeout = "30s"
          retries = {
            attempts      = 3
            perTryTimeout = "10s"
          }
        }
      ]
    }
  }

  depends_on = [helm_release.application]
}

# Apply ArgoCD Application
resource "kubernetes_manifest" "argocd_application" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name      = "automated-inquiries-processing"
      namespace = kubernetes_namespace.argocd.metadata[0].name
      finalizers = ["resources-finalizer.argocd.argoproj.io"]
    }
    spec = {
      project = "default"
      source = {
        repoURL        = "https://github.com/your-org/automated_inquiries_processing"
        targetRevision = "HEAD"
        path           = "k8s/helm"
        helm = {
          valueFiles = ["values.yaml"]
          parameters = [
            {
              name  = "image.tag"
              value = "latest"
            },
            {
              name  = "image.repository"
              value = "localhost:5000/automated-inquiries-processing"
            }
          ]
        }
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = kubernetes_namespace.inquiries_system.metadata[0].name
      }
      syncPolicy = {
        automated = {
          prune    = true
          selfHeal = true
        }
        syncOptions = [
          "CreateNamespace=true",
          "PrunePropagationPolicy=foreground",
          "PruneLast=true"
        ]
        retry = {
          limit = 5
          backoff = {
            duration    = "5s"
            factor      = 2
            maxDuration = "3m"
          }
        }
      }
      revisionHistoryLimit = 10
    }
  }

  depends_on = [helm_release.argocd]
}

# Outputs
output "service_urls" {
  description = "Application service URLs"
  value = {
    api = "http://localhost:30080"
    api_docs = "http://localhost:30080/docs"
    health_check = "http://localhost:30080/api/v1/health"
    mlflow = "http://localhost:30006"
    airflow = "http://localhost:30007"
  }
}

output "monitoring_urls" {
  description = "Monitoring service URLs"
  value = {
    grafana = "http://localhost:30001 (admin/admin)"
    prometheus = "http://localhost:30002"
    alertmanager = "http://localhost:30003"
    jaeger = "http://localhost:30004"
    fluentd = "http://localhost:30005"
  }
}

output "gitops_urls" {
  description = "GitOps service URLs"
  value = {
    argocd = "http://localhost:30000"
    argocd_admin_password = "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
  }
}

output "namespaces" {
  description = "Created namespaces"
  value = [
    kubernetes_namespace.inquiries_system.metadata[0].name,
    kubernetes_namespace.argocd.metadata[0].name,
    kubernetes_namespace.istio_system.metadata[0].name,
    kubernetes_namespace.monitoring.metadata[0].name
  ]
}
