# Monitoring and Alerting Guide

Comprehensive guide for monitoring the Inquiry Automation Pipeline and setting up effective alerting.

## Table of Contents

- [Overview](#overview)
- [Prometheus Metrics](#prometheus-metrics)
- [Grafana Dashboards](#grafana-dashboards)
- [Alerting Rules](#alerting-rules)
- [Custom Metrics](#custom-metrics)
- [Log Monitoring](#log-monitoring)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

The monitoring stack consists of:

### Local Development & AWS
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **Streamlit Dashboard**: Real-time business metrics
- **CloudWatch**: AWS service monitoring (production)

### Kubernetes Deployment (CNCF Stack)
- **Prometheus**: Kubernetes-native metrics collection
- **Grafana**: Containerized dashboards with persistent storage
- **Istio**: Service mesh observability and distributed tracing
- **Jaeger**: Distributed tracing (optional)
- **ArgoCD**: GitOps deployment monitoring
- **Kubernetes Metrics**: Pod, node, and cluster metrics

## Prometheus Metrics

### Metric Types

#### Counters
Track cumulative values that only increase:

```promql
# Total HTTP requests
http_requests_total

# Total inquiries processed
inquiries_processed_total

# Total model predictions
model_predictions_total
```

#### Gauges
Track values that can go up or down:

```promql
# Active database connections
db_connections_active

# System health status
system_health_status

# Current model version
model_version_info
```

#### Histograms
Track distribution of values:

```promql
# HTTP request duration
http_request_duration_seconds

# Model inference duration
model_inference_duration_seconds

# Database query duration
db_query_duration_seconds
```

### Key Metrics

#### API Metrics
```promql
# Request rate by endpoint
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Model Performance
```promql
# Average inference time
rate(model_inference_duration_seconds_sum[5m]) / rate(model_inference_duration_seconds_count[5m])

# Prediction confidence distribution
histogram_quantile(0.5, model_prediction_confidence_bucket)

# Model prediction rate
rate(model_predictions_total[5m])
```

#### Business Metrics
```promql
# Inquiry processing rate
rate(inquiries_processed_total{status="success"}[5m])

# Escalation rate
rate(routing_decisions_total{escalated="True"}[1h]) / rate(routing_decisions_total[1h])

# Category distribution
rate(inquiry_category_total[1h])
```

## Grafana Dashboards

### Dashboard Configuration

Dashboards are automatically provisioned from `monitoring/grafana/dashboards/`.

#### 1. Pipeline Overview Dashboard

**Purpose**: High-level system health and performance

**Panels**:
- Request rate (requests/second)
- Error rate percentage
- 95th percentile latency
- Active connections
- Service health status

**Refresh Rate**: 30 seconds

#### 2. Model Performance Dashboard

**Purpose**: ML model performance and accuracy

**Panels**:
- Model inference latency
- Prediction confidence distribution
- Category prediction accuracy
- Sentiment classification accuracy
- Urgency detection accuracy

**Refresh Rate**: 1 minute

#### 3. Business Metrics Dashboard

**Purpose**: Business KPIs and operational metrics

**Panels**:
- Inquiry volume over time
- Category distribution (pie chart)
- Department routing distribution
- Escalation rate trend
- Average priority score

**Refresh Rate**: 5 minutes

#### 4. System Health Dashboard

**Purpose**: Infrastructure and resource monitoring

**Panels**:
- CPU usage by service
- Memory usage by service
- Disk usage
- Database connection pool
- Network traffic

**Refresh Rate**: 30 seconds

### Custom Dashboard Creation

1. **Access Grafana**:
   ```bash
   # Local development
   open http://localhost:3000
   
   # Login: admin/admin
   ```

2. **Create Dashboard**:
   - Click "+" → "Dashboard"
   - Add panels with Prometheus queries
   - Configure alerts for critical metrics

3. **Export Dashboard**:
   ```bash
   # Save as JSON in monitoring/grafana/dashboards/
   # Will be automatically provisioned
   ```

## Alerting Rules

### Critical Alerts

#### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 5m
  labels:
    severity: critical
    component: api
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes"
```

#### Service Down
```yaml
- alert: ServiceDown
  expr: up == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.job }} is down"
    description: "{{ $labels.instance }} has been down for more than 2 minutes"
```

#### Database Connection Issues
```yaml
- alert: DatabaseConnectionIssues
  expr: db_connections_active == 0
  for: 1m
  labels:
    severity: critical
    component: database
  annotations:
    summary: "No active database connections"
    description: "The application has no active database connections"
```

### Warning Alerts

#### High Latency
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
  for: 5m
  labels:
    severity: warning
    component: api
  annotations:
    summary: "High API latency detected"
    description: "95th percentile latency is {{ $value }}s"
```

#### Low Model Confidence
```yaml
- alert: LowModelConfidence
  expr: avg(model_prediction_confidence) < 0.6
  for: 10m
  labels:
    severity: warning
    component: model
  annotations:
    summary: "Model confidence has dropped"
    description: "Average confidence is {{ $value | humanizePercentage }}"
```

#### High Escalation Rate
```yaml
- alert: HighEscalationRate
  expr: rate(routing_decisions_total{escalated="True"}[1h]) / rate(routing_decisions_total[1h]) > 0.2
  for: 30m
  labels:
    severity: warning
    component: routing
  annotations:
    summary: "Escalation rate is unusually high"
    description: "{{ $value | humanizePercentage }} of inquiries are being escalated"
```

### Alert Channels

#### Email Notifications
```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email-alerts'

receivers:
- name: 'email-alerts'
  email_configs:
  - to: 'alerts@company.com'
    subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
```

#### Slack Notifications
```yaml
receivers:
- name: 'slack-alerts'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts'
    title: 'Inquiry Pipeline Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## Custom Metrics

### Adding New Metrics

1. **Define Metric in Code**:
   ```python
   from prometheus_client import Counter, Histogram, Gauge

   # In src/monitoring/metrics.py
   custom_business_metric = Counter(
       'business_metric_total',
       'Description of business metric',
       ['category', 'department']
   )
   ```

2. **Record Metrics**:
   ```python
   # In your application code
   from src.monitoring.metrics import MetricsCollector

   MetricsCollector.record_custom_metric(
       category='technical_support',
       department='engineering'
   )
   ```

3. **Query in Grafana**:
   ```promql
   rate(business_metric_total[5m])
   ```

### Business-Specific Metrics

#### Customer Satisfaction
```python
customer_satisfaction_score = Gauge(
    'customer_satisfaction_score',
    'Customer satisfaction based on sentiment analysis',
    ['department']
)
```

#### Processing Efficiency
```python
processing_efficiency = Histogram(
    'inquiry_processing_efficiency',
    'Time from inquiry submission to resolution',
    buckets=(60, 300, 900, 3600, 14400)  # 1min, 5min, 15min, 1hr, 4hr
)
```

#### Model Accuracy
```python
model_accuracy = Gauge(
    'model_accuracy_score',
    'Model accuracy based on feedback',
    ['model_name', 'category']
)
```

## Log Monitoring

### Structured Logging

Configure structured logging for better monitoring:

```python
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)
logger.handlers[0].setFormatter(StructuredFormatter())
```

### Log Aggregation

#### Local Development
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api

# Search logs
docker-compose logs api | grep "ERROR"
```

#### Production (AWS)
```bash
# CloudWatch Logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/inquiry-automation"

# Stream logs
aws logs tail /ecs/inquiry-automation/api --follow

# Search logs
aws logs filter-log-events \
  --log-group-name "/ecs/inquiry-automation/api" \
  --filter-pattern "ERROR"
```

### Log Queries

#### Error Analysis
```bash
# Count errors by type
docker-compose logs api | grep "ERROR" | cut -d' ' -f4 | sort | uniq -c

# Find recent errors
docker-compose logs api --since 1h | grep "ERROR"
```

#### Performance Analysis
```bash
# Find slow requests
docker-compose logs api | grep "duration" | awk '$NF > 2.0'
```

## Performance Monitoring

### Key Performance Indicators (KPIs)

#### System Performance
- **Response Time**: 95th percentile < 2 seconds
- **Throughput**: > 100 inquiries/minute
- **Availability**: > 99.9% uptime
- **Error Rate**: < 1%

#### Model Performance
- **Inference Time**: < 500ms per inquiry
- **Accuracy**: > 85% category classification
- **Confidence**: > 70% average confidence

#### Business Performance
- **Processing Rate**: > 95% inquiries processed within SLA
- **Escalation Rate**: < 10% of inquiries escalated
- **Customer Satisfaction**: > 4.0/5.0 based on sentiment

### Performance Testing

#### Load Testing with Locust
```python
# locustfile.py
from locust import HttpUser, task, between

class InquiryUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def submit_inquiry(self):
        self.client.post("/api/v1/inquiries/submit", json={
            "subject": "Test inquiry",
            "body": "This is a test inquiry for load testing",
            "sender_email": "test@example.com"
        })
    
    @task(1)
    def get_stats(self):
        self.client.get("/api/v1/stats")
```

#### Run Load Test
```bash
# Install locust
pip install locust

# Run test
locust -f locustfile.py --host=http://localhost:8000

# Access web UI at http://localhost:8089
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_inquiries_timestamp ON inquiries(timestamp);
CREATE INDEX idx_predictions_category ON predictions(category);
CREATE INDEX idx_routing_department ON routing_decisions(department);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM inquiries WHERE processed = FALSE;
```

#### Model Optimization
```python
# Batch processing for better throughput
def batch_predict(texts, batch_size=32):
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_results = model.predict(batch)
        results.extend(batch_results)
    return results
```

#### Caching
```python
# Redis caching for frequent predictions
import redis
import hashlib
import json

cache = redis.Redis(host='localhost', port=6379, db=0)

def cached_predict(text, model_name):
    cache_key = f"{model_name}:{hashlib.md5(text.encode()).hexdigest()}"
    
    cached_result = cache.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    result = model.predict(text)
    cache.setex(cache_key, 3600, json.dumps(result))  # Cache for 1 hour
    return result
```

## Troubleshooting

### Common Monitoring Issues

#### 1. Metrics Not Appearing

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metric endpoints
curl http://localhost:8000/api/v1/metrics

# Verify scrape configuration
cat monitoring/prometheus/prometheus.yml
```

#### 2. Grafana Dashboard Issues

```bash
# Check data source connection
# Go to Grafana → Configuration → Data Sources

# Test Prometheus query
# Use Grafana's query inspector

# Check dashboard JSON syntax
cat monitoring/grafana/dashboards/pipeline-overview.json | jq .
```

#### 3. Alert Not Firing

```bash
# Check alert rule syntax
promtool check rules monitoring/prometheus/alerts.yml

# Test alert expression
# Go to Prometheus → Alerts → Test expression

# Check Alertmanager configuration
promtool check config monitoring/alertmanager/alertmanager.yml
```

### Monitoring Best Practices

#### 1. Metric Naming
- Use descriptive names: `inquiry_processing_duration_seconds`
- Include units: `_seconds`, `_bytes`, `_total`
- Use consistent naming conventions

#### 2. Label Usage
- Keep cardinality low (< 100 unique combinations)
- Use labels for dimensions: `{category="billing", urgency="high"}`
- Avoid high-cardinality labels like user IDs

#### 3. Alert Fatigue Prevention
- Set appropriate thresholds
- Use grouping to reduce noise
- Implement alert suppression
- Regular alert review and cleanup

#### 4. Dashboard Design
- Keep dashboards focused on specific use cases
- Use appropriate visualization types
- Include context and time ranges
- Regular dashboard maintenance

### Emergency Procedures

#### 1. Service Degradation
1. Check Grafana dashboards for anomalies
2. Review recent deployments
3. Check resource utilization
4. Scale services if needed

#### 2. Complete Service Failure
1. Check health endpoints
2. Review service logs
3. Check infrastructure status
4. Execute rollback procedures

#### 3. Data Issues
1. Check database connectivity
2. Verify data integrity
3. Review recent data processing
4. Restore from backup if necessary

## Monitoring Checklist

### Daily
- [ ] Check system health dashboards
- [ ] Review error rates and alerts
- [ ] Monitor key business metrics
- [ ] Verify backup completion

### Weekly
- [ ] Review alert effectiveness
- [ ] Analyze performance trends
- [ ] Check capacity utilization
- [ ] Update monitoring documentation

### Monthly
- [ ] Review and optimize dashboards
- [ ] Clean up old alerts
- [ ] Capacity planning review
- [ ] Disaster recovery testing

## Support Contacts

- **Monitoring Team**: monitoring@company.com
- **DevOps Team**: devops@company.com
- **On-Call Engineer**: +1-XXX-XXX-XXXX

## Kubernetes Monitoring (CNCF Stack)

### Service Mesh Observability

#### Istio Metrics

Istio automatically exposes comprehensive metrics for service mesh observability:

```promql
# Request rate by service and destination
rate(istio_requests_total[5m])

# Request duration percentiles
histogram_quantile(0.95, rate(istio_request_duration_milliseconds_bucket[5m]))

# Error rate by service
rate(istio_requests_total{response_code=~"5.."}[5m]) / rate(istio_requests_total[5m])

# Service mesh health
up{job="istio-mesh"}

# Traffic distribution
sum(rate(istio_requests_total[5m])) by (destination_service_name)
```

#### Distributed Tracing

Enable Jaeger for distributed tracing:

```bash
# Install Jaeger
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.17/samples/addons/jaeger.yaml

# Access Jaeger UI
kubectl port-forward -n istio-system svc/jaeger 16686:80
```

### Kubernetes Cluster Metrics

#### Node and Pod Metrics

```promql
# CPU usage by pod
rate(container_cpu_usage_seconds_total[5m])

# Memory usage by container
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100

# Pod restart frequency
rate(kube_pod_container_status_restarts_total[5m])

# Node resource utilization
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Storage usage
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100
```

#### Application-Specific Metrics

```promql
# Pod health status
kube_pod_status_phase{namespace="inquiries-system"}

# Deployment replica status
kube_deployment_status_replicas_available / kube_deployment_status_replicas_desired * 100

# Service endpoint availability
up{job="kubernetes-service-endpoints", namespace="inquiries-system"}
```

### GitOps Monitoring with ArgoCD

#### ArgoCD Application Metrics

```bash
# Check application sync status
kubectl get applications -n argocd -o jsonpath='{.items[*].status.sync.status}'

# Monitor deployment health
kubectl get applications -n argocd -o jsonpath='{.items[*].status.health.status}'

# Check sync history
kubectl describe application inquiries-automation -n argocd
```

#### ArgoCD Alerts

```yaml
# Alert for failed ArgoCD syncs
- alert: ArgoCDSyncFailed
  expr: argocd_app_info{sync_status="OutOfSync"} == 1
  for: 5m
  labels:
    severity: warning
    component: argocd
  annotations:
    summary: "ArgoCD application is out of sync"
    description: "Application {{ $labels.name }} has been out of sync for more than 5 minutes"

# Alert for ArgoCD sync errors
- alert: ArgoCDSyncError
  expr: argocd_app_info{health_status="Degraded"} == 1
  for: 2m
  labels:
    severity: critical
    component: argocd
  annotations:
    summary: "ArgoCD application is degraded"
    description: "Application {{ $labels.name }} health status is degraded"
```

### Kubernetes Dashboard Configuration

#### Cluster Overview Dashboard

Create a Grafana dashboard for Kubernetes cluster monitoring:

```json
{
  "dashboard": {
    "title": "Kubernetes Cluster Overview",
    "panels": [
      {
        "title": "CPU Usage by Namespace",
        "targets": [
          {
            "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) by (namespace)",
            "legendFormat": "{{namespace}}"
          }
        ]
      },
      {
        "title": "Memory Usage by Pod",
        "targets": [
          {
            "expr": "sum(container_memory_usage_bytes) by (pod, namespace)",
            "legendFormat": "{{namespace}}/{{pod}}"
          }
        ]
      }
    ]
  }
}
```

#### Service Mesh Dashboard

```json
{
  "dashboard": {
    "title": "Istio Service Mesh",
    "panels": [
      {
        "title": "Request Rate by Service",
        "targets": [
          {
            "expr": "sum(rate(istio_requests_total[5m])) by (destination_service_name)",
            "legendFormat": "{{destination_service_name}}"
          }
        ]
      },
      {
        "title": "Request Duration P95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(istio_request_duration_milliseconds_bucket[5m]))",
            "legendFormat": "P95 Latency"
          }
        ]
      }
    ]
  }
}
```

### Kubernetes-Specific Alerts

```yaml
# High CPU usage on nodes
- alert: HighNodeCPUUsage
  expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High CPU usage on node {{ $labels.instance }}"

# Pod restart frequency
- alert: HighPodRestartRate
  expr: rate(kube_pod_container_status_restarts_total[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High restart rate for pod {{ $labels.pod }}"

# Service mesh error rate
- alert: HighServiceMeshErrorRate
  expr: rate(istio_requests_total{response_code=~"5.."}[5m]) / rate(istio_requests_total[5m]) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate in service mesh"
```

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Alerting Best Practices](https://prometheus.io/docs/practices/alerting/)
- [Istio Observability](https://istio.io/latest/docs/ops/observability/)
- [Kubernetes Monitoring Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)
- [ArgoCD Monitoring](https://argo-cd.readthedocs.io/en/stable/operator-manual/monitoring/)
