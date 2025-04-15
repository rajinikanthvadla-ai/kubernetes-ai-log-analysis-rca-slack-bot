import os
import time
import random
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from prometheus_client import Counter, start_http_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
request_counter = Counter('load_generator_requests_total', 'Total requests made by load generator')
error_counter = Counter('load_generator_errors_total', 'Total errors encountered by load generator')

def make_request():
    target_service = os.environ.get('TARGET_SERVICE', 'http://service1:8000')
    endpoints = ['/', '/random-error']
    
    try:
        endpoint = random.choice(endpoints)
        response = requests.get(f"{target_service}{endpoint}")
        response.raise_for_status()
        request_counter.inc()
        logger.info(f"Request to {endpoint} successful")
    except Exception as e:
        error_counter.inc()
        logger.error(f"Error making request: {e}")

def main():
    # Start Prometheus metrics server
    start_http_server(8000)
    
    rps = int(os.environ.get('RPS', 10))
    logger.info(f"Starting load generator with {rps} requests per second")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            for _ in range(rps):
                executor.submit(make_request)
            time.sleep(1)

if __name__ == "__main__":
    main() 