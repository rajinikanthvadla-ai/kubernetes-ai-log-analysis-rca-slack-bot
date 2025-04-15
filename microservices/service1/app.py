from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import random
import logging

app = FastAPI()

# Metrics
request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    with request_latency.labels(method='GET', endpoint='/').time():
        request_counter.labels(method='GET', endpoint='/').inc()
        logger.info("Root endpoint accessed")
        return {"message": "Hello from Service 1"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/random-error")
async def random_error():
    with request_latency.labels(method='GET', endpoint='/random-error').time():
        request_counter.labels(method='GET', endpoint='/random-error').inc()
        if random.random() < 0.3:
            logger.error("Random error occurred")
            raise Exception("Random error occurred")
        return {"message": "No error this time"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 