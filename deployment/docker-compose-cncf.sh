#!/bin/bash
# Docker Compose setup with CNCF services simulation
# This provides a local development environment that mimics Kubernetes + CNCF services

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Docker Compose with CNCF Services Simulation${NC}"
echo "=================================================="
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"

# Create CNCF services simulation
echo -e "${YELLOW}Creating CNCF services simulation...${NC}"

# Create a mock Istio Gateway simulation
cat > docker-compose.cncf.yml << 'EOF'
version: '3.8'

services:
  # Mock Istio Gateway
  istio-gateway:
    image: nginx:alpine
    container_name: istio-gateway
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/istio-gateway.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
    networks:
      - inquiry_network

  # Mock ArgoCD UI simulation
  argocd-mock:
    image: nginx:alpine
    container_name: argocd-mock
    ports:
      - "8080:80"
    volumes:
      - ./deployment/nginx/argocd-mock.conf:/etc/nginx/nginx.conf
      - ./deployment/nginx/argocd-ui:/usr/share/nginx/html
    networks:
      - inquiry_network

  # Jaeger for distributed tracing (Istio alternative)
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - inquiry_network

  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: otel-collector
    ports:
      - "4317:4317"
      - "4318:4318"
    volumes:
      - ./deployment/otel/otel-collector-config.yml:/etc/otelcol-contrib/otel-collector-config.yml
    networks:
      - inquiry_network

  # Fluentd for log aggregation
  fluentd:
    image: fluent/fluentd:v1.16-debian-1
    container_name: fluentd
    ports:
      - "24224:24224"
    volumes:
      - ./deployment/fluentd/fluent.conf:/fluentd/etc/fluent.conf
    networks:
      - inquiry_network

  # Elasticsearch for log storage
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    networks:
      - inquiry_network

  # Kibana for log visualization
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - inquiry_network

networks:
  inquiry_network:
    external: true
EOF

# Create configuration files
mkdir -p deployment/nginx deployment/otel deployment/fluentd

# Istio Gateway simulation
cat > deployment/nginx/istio-gateway.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # Simulate Istio Gateway functionality
        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Add Istio-like headers
            proxy_set_header X-Envoy-External-Address $remote_addr;
            proxy_set_header X-Request-Id $request_id;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://api_backend/api/v1/health;
        }
    }
}
EOF

# ArgoCD Mock UI
cat > deployment/nginx/argocd-mock.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF

# Create a simple ArgoCD mock UI
mkdir -p deployment/nginx/argocd-ui
cat > deployment/nginx/argocd-ui/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>ArgoCD Mock UI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #ef7b4d; color: white; padding: 20px; border-radius: 5px; }
        .app { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .status { padding: 5px 10px; border-radius: 3px; color: white; }
        .healthy { background: #28a745; }
        .syncing { background: #ffc107; color: black; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 ArgoCD Mock UI</h1>
        <p>GitOps Continuous Deployment Dashboard</p>
    </div>
    
    <h2>Applications</h2>
    
    <div class="app">
        <h3>automated-inquiries-processing</h3>
        <p><strong>Repository:</strong> https://github.com/your-org/automated_inquiries_processing</p>
        <p><strong>Path:</strong> k8s/helm</p>
        <p><strong>Status:</strong> <span class="status healthy">Healthy</span></p>
        <p><strong>Last Sync:</strong> 2024-01-15 10:30:00</p>
    </div>
    
    <div class="app">
        <h3>monitoring-stack</h3>
        <p><strong>Repository:</strong> https://github.com/your-org/automated_inquiries_processing</p>
        <p><strong>Path:</strong> monitoring/helm</p>
        <p><strong>Status:</strong> <span class="status syncing">Syncing</span></p>
        <p><strong>Last Sync:</strong> 2024-01-15 10:25:00</p>
    </div>
    
    <h2>CNCF Services Status</h2>
    <ul>
        <li>✅ Istio Gateway: Running (Port 80/443)</li>
        <li>✅ Prometheus: Running (Port 9090)</li>
        <li>✅ Grafana: Running (Port 3000)</li>
        <li>✅ Jaeger: Running (Port 16686)</li>
        <li>✅ Fluentd: Running (Port 24224)</li>
        <li>✅ Elasticsearch: Running (Port 9200)</li>
        <li>✅ Kibana: Running (Port 5601)</li>
    </ul>
</body>
</html>
EOF

# OpenTelemetry Collector configuration
cat > deployment/otel/otel-collector-config.yml << 'EOF'
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
EOF

# Fluentd configuration
cat > deployment/fluentd/fluent.conf << 'EOF'
<source>
  @type forward
  port 24224
</source>

<match **>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name fluentd
  type_name fluentd
</match>
EOF

echo -e "${GREEN}✓ CNCF services simulation created${NC}"

# Start the services
echo -e "${YELLOW}Starting Docker Compose services...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.cncf.yml up -d

echo -e "${GREEN}✓ All services started${NC}"

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 30

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Docker Compose + CNCF Services Ready!${NC}"
echo "=================================================="
echo ""

echo "🌐 Application URLs:"
echo "  • API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/api/v1/health"
echo ""

echo "📊 CNCF Services URLs:"
echo "  • Istio Gateway: http://localhost:80"
echo "  • ArgoCD Mock UI: http://localhost:8080"
echo "  • Grafana: http://localhost:3000 (admin/admin)"
echo "  • Prometheus: http://localhost:9090"
echo "  • MLflow: http://localhost:5001"
echo "  • Jaeger Tracing: http://localhost:16686"
echo "  • Elasticsearch: http://localhost:9200"
echo "  • Kibana: http://localhost:5601"
echo ""

echo "🔧 Management Commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Restart services: docker-compose restart"
echo "  • View containers: docker ps"
echo ""

echo "📚 Next Steps:"
echo "  1. Test the API endpoints"
echo "  2. Explore the monitoring dashboards"
echo "  3. Check distributed tracing in Jaeger"
echo "  4. View logs in Kibana"
echo "  5. Simulate GitOps workflow with ArgoCD mock"
echo ""
