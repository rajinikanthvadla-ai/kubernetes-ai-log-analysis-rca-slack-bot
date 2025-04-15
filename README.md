# Kubernetes AI Log Analysis RCA Slack Bot

This project provides a comprehensive solution for monitoring Kubernetes clusters, analyzing logs, and performing root cause analysis using AI. It includes a Slack bot for easy interaction and a load generator for testing.

## Prerequisites

### 1. System Requirements
- Windows 10/11 or Linux/MacOS
- Minimum 8GB RAM
- 20GB free disk space
- CPU with virtualization support enabled

### 2. Required Software
1. **Docker Desktop**
   ```bash
   # Windows: Download from https://www.docker.com/products/docker-desktop
   # Linux: 
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   # Verify installation
   docker --version
   ```

2. **kubectl**
   ```bash
   # Windows: Download from https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/
   # Linux:
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   # Verify installation
   kubectl version --client
   ```

3. **Helm**
   ```bash
   # Windows: Download from https://github.com/helm/helm/releases
   # Linux:
   curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
   chmod 700 get_helm.sh
   ./get_helm.sh
   # Verify installation
   helm version
   ```

4. **Python 3.8+**
   ```bash
   # Windows: Download from https://www.python.org/downloads/
   # Linux:
   sudo apt update
   sudo apt install python3 python3-pip
   # Verify installation
   python3 --version
   pip3 --version
   ```

5. **Git**
   ```bash
   # Windows: Download from https://git-scm.com/download/win
   # Linux:
   sudo apt install git
   # Verify installation
   git --version
   ```

## Step-by-Step Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/kubernetes-ai-log-analysis-rca-slack-bot.git
cd kubernetes-ai-log-analysis-rca-slack-bot
```

### 2. Create and Configure Environment Variables
```bash
# Create .env file
touch .env

# Edit .env file with your credentials
nano .env  # or use any text editor
```

Add the following content to `.env`:
```bash
# 🔐 Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your-webhook
SLACK_CHANNEL=aiops

# 🤖 HuggingFace LLM API
HUGGINGFACE_API_KEY=your-huggingface-api-key
HUGGINGFACE_MODEL=deepseek/deepseek-v3-0324
HUGGINGFACE_API_URL=https://router.huggingface.co/novita/v3/openai/chat/completions

# 🚀 Kubernetes Configuration
KIND_CLUSTER_NAME=aiops-lab
KUBECONFIG=~/.kube/config
```

### 3. Build and Push Docker Images

1. **Login to Docker Hub**
```bash
# Create a Docker Hub account at https://hub.docker.com
docker login
# Enter your Docker Hub username and password
```

2. **Build and Push AIOps Bot**
```bash
cd aiops-bot
docker build -t rajiniops/aiops-bot:latest .
docker push rajiniops/aiops-bot:latest
# Verify push
docker images | grep aiops-bot
```

3. **Build and Push Load Generator**
```bash
cd ../load-generator
docker build -t rajiniops/load-generator:latest .
docker push rajiniops/load-generator:latest
# Verify push
docker images | grep load-generator
```

4. **Build and Push Sample Service**
```bash
cd ../microservices/service1
docker build -t rajiniops/sample-service:latest .
docker push rajiniops/sample-service:latest
# Verify push
docker images | grep sample-service
```

5. **Update Deployment Configurations**
```bash
# Make the script executable
chmod +x update-deployments.sh

# Run the script with your Docker Hub username
./update-deployments.sh rajiniops
```

### 4. Create Kubernetes Cluster

1. **Create KIND Cluster**
```bash
# Create cluster configuration
cat > kind-config.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 31022
    hostPort: 31022
  - containerPort: 3000
    hostPort: 3000
  - containerPort: 9090
    hostPort: 9090
  - containerPort: 9093
    hostPort: 9093
EOF

# Create cluster
kind create cluster --name $KIND_CLUSTER_NAME --config kind-config.yaml

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### 5. Deploy Monitoring Stack

1. **Create Namespaces**
```bash
kubectl create namespace monitoring
kubectl create namespace aiops-bot
kubectl create namespace microservices
```

2. **Deploy Prometheus**
```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.service.type=NodePort \
  --set prometheus.service.nodePort=9090 \
  --set grafana.service.type=NodePort \
  --set grafana.service.nodePort=3000 \
  --set alertmanager.service.type=NodePort \
  --set alertmanager.service.nodePort=9093
```

3. **Verify Monitoring Stack**
```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

### 6. Deploy Microservices

1. **Deploy Sample Service**
```bash
kubectl apply -f microservices/service1/deployment.yaml -n microservices
kubectl apply -f microservices/service1/service.yaml -n microservices
```

2. **Deploy Load Generator**
```bash
kubectl apply -f load-generator/deployment.yaml -n microservices
```

3. **Verify Microservices**
```bash
kubectl get pods -n microservices
kubectl get svc -n microservices
```

### 7. Deploy AIOps Bot

1. **Create Kubernetes Secret**
```bash
kubectl create secret generic slack-bot-secrets -n aiops-bot \
  --from-literal=SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  --from-literal=SLACK_APP_TOKEN=$SLACK_APP_TOKEN \
  --from-literal=HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY \
  --from-literal=HUGGINGFACE_MODEL=$HUGGINGFACE_MODEL \
  --from-literal=HUGGINGFACE_API_URL=$HUGGINGFACE_API_URL
```

2. **Deploy Bot**
```bash
kubectl apply -f aiops-bot/rbac.yaml -n aiops-bot
kubectl apply -f aiops-bot/deployment.yaml -n aiops-bot
```

3. **Verify Bot Deployment**
```bash
kubectl get pods -n aiops-bot
kubectl logs -n aiops-bot deployment/aiops-bot
```

## Accessing Services

1. **Grafana Dashboard**
   - URL: http://localhost:3000
   - Default credentials: admin/prom-operator
   - Import dashboards from `monitoring/dashboards/`

2. **Prometheus**
   - URL: http://localhost:9090
   - Access metrics and alerts

3. **Alertmanager**
   - URL: http://localhost:9093
   - Configure alert notifications

4. **Sample Service**
   - URL: http://localhost:31022/service1
   - Test endpoint: http://localhost:31022/service1/metrics

## Alert Rules Configuration

1. **Create Alert Rules**
```bash
kubectl apply -f monitoring/microservices-alerts.yaml -n monitoring
```

2. **Verify Alerts**
```bash
kubectl get prometheusrules -n monitoring
```

## Troubleshooting

### Common Issues and Solutions

1. **Docker Image Build Failures**
   ```bash
   # Check Docker daemon
   docker info
   
   # Clean up Docker
   docker system prune -a
   
   # Retry build with verbose output
   docker build -t aiops-bot:latest . --progress=plain
   ```

2. **Kubernetes Cluster Issues**
   ```bash
   # Check cluster status
   kubectl get nodes
   
   # Check pod status
   kubectl get pods --all-namespaces
   
   # Check events
   kubectl get events --all-namespaces
   ```

3. **Monitoring Stack Issues**
   ```bash
   # Check Prometheus logs
   kubectl logs -n monitoring deployment/prometheus-operator
   
   # Check Grafana logs
   kubectl logs -n monitoring deployment/prometheus-grafana
   
   # Check Alertmanager logs
   kubectl logs -n monitoring deployment/prometheus-alertmanager
   ```

4. **Slack Bot Issues**
   ```bash
   # Check bot logs
   kubectl logs -n aiops-bot deployment/aiops-bot
   
   # Verify secrets
   kubectl get secret slack-bot-secrets -n aiops-bot -o yaml
   
   # Restart bot
   kubectl rollout restart deployment aiops-bot -n aiops-bot
   ```

## Maintenance

1. **Update Images**
```bash
# Pull latest changes
git pull

# Rebuild and update images
docker build -t aiops-bot:latest aiops-bot/
docker build -t load-generator:latest load-generator/
docker build -t sample-service:latest microservices/service1/

# Update deployments
kubectl rollout restart deployment aiops-bot -n aiops-bot
kubectl rollout restart deployment load-generator -n microservices
kubectl rollout restart deployment service1 -n microservices
```

2. **Cleanup**
```bash
# Delete cluster
kind delete cluster --name $KIND_CLUSTER_NAME

# Clean Docker
docker system prune -a

# Remove local files
rm -rf .env kind-config.yaml
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 