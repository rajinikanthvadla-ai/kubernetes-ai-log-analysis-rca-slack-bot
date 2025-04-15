#!/bin/bash

# Check if Docker Hub username is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <dockerhub-username>"
    exit 1
fi

DOCKERHUB_USERNAME=$1

# Update AIOps Bot deployment
sed -i "s|image: aiops-bot:latest|image: ${DOCKERHUB_USERNAME}/aiops-bot:latest|g" aiops-bot/deployment.yaml

# Update Load Generator deployment
sed -i "s|image: load-generator:latest|image: ${DOCKERHUB_USERNAME}/load-generator:latest|g" load-generator/deployment.yaml

# Update Sample Service deployment
sed -i "s|image: sample-service:latest|image: ${DOCKERHUB_USERNAME}/sample-service:latest|g" microservices/service1/deployment.yaml

echo "Deployment configurations updated successfully with Docker Hub username: ${DOCKERHUB_USERNAME}" 