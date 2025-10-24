#!/bin/bash

echo "🎉 Your Complete Kubernetes Deployment is Ready!"
echo "================================================"

echo -e "\n📊 DEPLOYED SERVICES:"
echo "====================="

echo -e "\n✅ Core Applications:"
echo "  • Streamlit Dashboard (Monitoring & Analytics)"
echo "  • FastAPI Application (REST API)"
echo "  • PostgreSQL Database (Data Storage)"
echo "  • Redis Cache (Session & Caching)"

echo -e "\n✅ CNCF Services:"
echo "  • Istio Service Mesh (Traffic Management)"
echo "  • ArgoCD (GitOps Platform)"
echo "  • Prometheus (Metrics Collection)"
echo "  • Grafana (Dashboards & Visualization)"
echo "  • AlertManager (Alert Management)"

echo -e "\n🌐 ACCESS YOUR SERVICES:"
echo "========================="

echo -e "\n1. 📊 Streamlit Dashboard (Main App):"
echo "   kubectl port-forward -n inquiries-system svc/streamlit-dashboard 8501:8501"
echo "   Then visit: http://localhost:8501"
echo "   This shows your inquiry automation pipeline dashboard!"

echo -e "\n2. 🔌 FastAPI Application (API):"
echo "   kubectl port-forward -n inquiries-system svc/fastapi-app 8000:8000"
echo "   Then visit: http://localhost:8000/docs"
echo "   This provides REST API endpoints for your application!"

echo -e "\n3. 📈 Grafana Dashboards:"
echo "   kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
echo "   Then visit: http://localhost:3000 (admin/admin)"
echo "   This shows system monitoring dashboards!"

echo -e "\n4. 📊 Prometheus Metrics:"
echo "   kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "   Then visit: http://localhost:9090"
echo "   This shows metrics collection!"

echo -e "\n5. 🚨 AlertManager:"
echo "   kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093"
echo "   Then visit: http://localhost:9093"
echo "   This manages alerts!"

echo -e "\n6. 🔄 ArgoCD GitOps:"
echo "   kubectl port-forward -n argocd svc/argocd-server 8080:80"
echo "   Then visit: http://localhost:8080"
echo "   This manages your GitOps workflows!"

echo -e "\n📋 QUICK START:"
echo "==============="
echo "1. Start the Streamlit dashboard:"
echo "   kubectl port-forward -n inquiries-system svc/streamlit-dashboard 8501:8501"
echo ""
echo "2. Open your browser to: http://localhost:8501"
echo ""
echo "3. Explore your inquiry automation pipeline!"

echo -e "\n🎯 WHAT YOU CAN DO:"
echo "==================="
echo "• Monitor inquiry processing pipeline"
echo "• View analytics and metrics"
echo "• Submit test inquiries via API"
echo "• Track model performance"
echo "• Manage routing decisions"
echo "• View system health metrics"

echo -e "\n🔧 DATABASE ACCESS:"
echo "==================="
echo "PostgreSQL: postgresql.inquiries-system.svc.cluster.local:5432"
echo "Redis: redis-master.inquiries-system.svc.cluster.local:6379"

echo -e "\n✨ Your Kubernetes deployment with CNCF services is complete!"
echo "All services are running and ready to use! 🚀"
