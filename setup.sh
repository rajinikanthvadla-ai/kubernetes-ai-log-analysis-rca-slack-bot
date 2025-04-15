#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and fill in the values."
    exit 1
fi
source .env

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is required but not installed."
        exit 1
    fi
}

# Check required commands
check_command kind
check_command kubectl
check_command helm
check_command docker

# Create KIND cluster
echo "Creating KIND cluster..."
kind create cluster --name $KIND_CLUSTER_NAME --config kind-config.yaml

# Wait for cluster to be ready
echo "Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready node --all --timeout=300s

# Create namespaces
echo "Creating namespaces..."
kubectl create namespace monitoring
kubectl create namespace microservices
kubectl create namespace aiops-bot

# Setup ingress
echo "Setting up ingress..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

# Deploy monitoring stack
echo "Deploying monitoring stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values monitoring/prometheus-values.yaml \
  --set alertmanager.config.global.slack_api_url=$SLACK_WEBHOOK_URL

# Install Grafana
helm upgrade --install grafana grafana/grafana \
  --namespace monitoring \
  --values monitoring/grafana-values.yaml

# Install Loki
helm upgrade --install loki grafana/loki \
  --namespace monitoring \
  --values monitoring/loki-values.yaml

# Deploy microservices
echo "Deploying microservices..."
kubectl apply -f microservices/ -n microservices

# Deploy Slack bot
echo "Deploying Slack bot..."
kubectl create secret generic slack-bot-secrets \
  --namespace aiops-bot \
  --from-literal=SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  --from-literal=SLACK_APP_TOKEN=$SLACK_APP_TOKEN \
  --from-literal=HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY \
  --from-literal=HUGGINGFACE_MODEL=$HUGGINGFACE_MODEL \
  --from-literal=HUGGINGFACE_API_URL=$HUGGINGFACE_API_URL

kubectl apply -f aiops-bot/ -n aiops-bot

# Deploy load generator
echo "Deploying load generator..."
kubectl apply -f load-generator/ -n microservices

# Wait for all pods to be ready
echo "Waiting for all pods to be ready..."
kubectl wait --for=condition=Ready pod --all --all-namespaces --timeout=300s

# Print access information
echo "Setup completed successfully!"
echo "Grafana URL: http://localhost:3000"
echo "Prometheus URL: http://localhost:9090"
echo "Loki URL: http://localhost:3100"
echo "Slack Bot is ready to receive commands in the #$SLACK_CHANNEL channel" 