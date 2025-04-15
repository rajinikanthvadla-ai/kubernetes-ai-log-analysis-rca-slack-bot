# 🧠 AIOps Monitoring Lab

An end-to-end observability lab with AI-powered Slack Bot on Kubernetes, featuring automated monitoring, logging, and root cause analysis.

## 🚀 Features

- Kubernetes cluster setup with KIND
- Complete observability stack:
  - Prometheus for metrics
  - Grafana for visualization
  - Loki for logs
  - Alertmanager for alerts
- Sample microservices with metrics endpoints
- AI-powered Slack bot for:
  - Log retrieval
  - Root cause analysis using HuggingFace LLM
- Automated load generation for testing
- Everything as code with zero manual setup

## 📋 Prerequisites

- Docker Desktop
- KIND
- kubectl
- Helm
- Python 3.9+

## 🛠️ Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` with your:
   - Slack bot tokens
   - HuggingFace API key
   - Other configuration

4. Run the setup script:
   ```bash
   ./setup.sh
   ```

## 📊 Accessing the Stack

After setup, you can access:

- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

## 🤖 Using the Slack Bot

The Slack bot supports two commands:

1. `/getlogs <namespace> <pod>` - Retrieve logs for a specific pod
2. `/rca <namespace> <pod>` - Perform root cause analysis on pod logs

## 🔍 Monitoring

The stack includes pre-configured dashboards for:
- Cluster health
- Node/pod/namespace metrics
- Service performance
- Error rates

## 🚨 Alerts

Alerts are configured for:
- Pod restarts
- High CPU load
- Service downtime
- Error rates

## 🧪 Load Testing

A load generator is included to test the system:
- Configurable RPS (requests per second)
- Random error injection
- Metrics collection

## 📁 Project Structure

```
.
├── .env.example              # Environment variables template
├── setup.sh                  # Main setup script
├── kind-config.yaml          # KIND cluster configuration
├── monitoring/               # Monitoring stack configuration
│   ├── prometheus-values.yaml
│   ├── grafana-values.yaml
│   └── loki-values.yaml
├── microservices/           # Sample microservices
│   └── service1/
│       ├── app.py
│       ├── Dockerfile
│       └── deployment.yaml
├── aiops-bot/              # Slack bot
│   ├── app.py
│   ├── Dockerfile
│   └── deployment.yaml
└── load-generator/         # Load testing
    ├── app.py
    ├── Dockerfile
    └── deployment.yaml
```

## 🔧 Troubleshooting

If you encounter issues:

1. Check pod status:
   ```bash
   kubectl get pods -A
   ```

2. View logs:
   ```bash
   kubectl logs -n <namespace> <pod-name>
   ```

3. Check Slack bot status:
   ```bash
   kubectl logs -n aiops-bot deployment/aiops-bot
   ```

## 📝 License

MIT License 