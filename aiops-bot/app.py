import os
import logging
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from kubernetes import client, config
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

# Debug environment variables
logger.info("Environment variables:")
logger.info(f"SLACK_BOT_TOKEN: {os.environ.get('SLACK_BOT_TOKEN', 'not set')[:10]}...")
logger.info(f"SLACK_APP_TOKEN: {os.environ.get('SLACK_APP_TOKEN', 'not set')[:10]}...")
logger.info(f"HUGGINGFACE_API_KEY: {os.environ.get('HUGGINGFACE_API_KEY', 'not set')[:10]}...")

try:
    # Initialize Slack app
    app = App(token=os.environ["SLACK_BOT_TOKEN"])
    logger.info("Slack app initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Slack app: {e}")
    raise

# Load Kubernetes config
try:
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    logger.info("Kubernetes client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Kubernetes client: {e}")
    raise

# HuggingFace API configuration
HF_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
if not HF_API_KEY:
    logger.error("HUGGINGFACE_API_KEY not set")
    raise ValueError("HUGGINGFACE_API_KEY environment variable is required")

HF_MODEL = os.environ.get("HUGGINGFACE_MODEL", "deepseek/deepseek-v3-0324")
HF_API_URL = os.environ.get("HUGGINGFACE_API_URL", "https://router.huggingface.co/novita/v3/openai/chat/completions")

def analyze_logs_with_llm(logs):
    """Analyze logs using HuggingFace API"""
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""As an experienced DevOps engineer, analyze these Kubernetes logs and provide a root cause analysis:

{logs}

Please provide a concise analysis focusing on:
1. Error patterns
2. Potential causes
3. Recommended actions"""

    data = {
        "model": HF_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Handle different response formats
        if isinstance(result, dict):
            # Try OpenAI format
            if "choices" in result:
                choices = result.get("choices", [])
                if choices and isinstance(choices, list):
                    choice = choices[0]
                    if isinstance(choice, dict):
                        if "message" in choice:
                            message = choice["message"]
                            if isinstance(message, dict) and "content" in message:
                                return message["content"]
                        elif "text" in choice:
                            return choice["text"]
            
            # Try direct text response
            if "text" in result and isinstance(result["text"], str):
                return result["text"]
            
            # Try HuggingFace format
            if "generated_text" in result and isinstance(result["generated_text"], str):
                return result["generated_text"]
            
            # Try to find any text content in the response
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 50:
                    return value
            
            # If no text found, return the whole response as string
            return str(result)
            
        elif isinstance(result, list):
            # Handle list responses
            for item in result:
                if isinstance(item, str):
                    return item
                elif isinstance(item, dict):
                    for key, value in item.items():
                        if isinstance(value, str) and len(value) > 50:
                            return value
            
            # If no text found in list items, return the first item as string
            if result:
                return str(result[0])
            
        return "Analysis completed, but response format was unexpected."
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling HuggingFace API: {e}")
        return f"Error connecting to analysis service: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing HuggingFace API response: {e}")
        return f"Error analyzing logs: {str(e)}"

@app.command("/getlogs")
def get_logs(ack, command, say):
    ack()
    
    try:
        # Get the command text
        cmd_text = command.get('text', '').strip()
        
        if not cmd_text:
            # Get all pods in all namespaces
            pods = v1.list_pod_for_all_namespaces()
            output = []
            
            for pod in pods.items:
                try:
                    # Get pod logs
                    logs = v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=pod.metadata.namespace,
                        tail_lines=50
                    )
                    output.append(f"=== {pod.metadata.namespace}/{pod.metadata.name} ===\n{logs}\n")
                except Exception as e:
                    logger.error(f"Error getting logs for {pod.metadata.namespace}/{pod.metadata.name}: {e}")
                    continue
            
            if not output:
                say("No pods found or no logs available")
                return
                
            # Combine all logs
            result = "\n".join(output)
            if len(result) > 3000:
                result = result[:3000] + "\n... (truncated)"
            
            say(result)
            
        else:
            # Specific pod logs
            try:
                namespace, pod = cmd_text.split('/')
                logs = v1.read_namespaced_pod_log(
                    name=pod,
                    namespace=namespace,
                    tail_lines=200
                )
                
                if len(logs) > 3000:
                    logs = logs[:3000] + "\n... (truncated)"
                
                say(f"=== {namespace}/{pod} ===\n{logs}")
                
            except ValueError:
                say("Usage: /getlogs [namespace/pod] or just /getlogs for all pod logs")
                return
            except Exception as e:
                say(f"Error getting logs: {str(e)}")
                return
        
    except Exception as e:
        logger.error(f"Error in getlogs command: {e}")
        say(f"Error: {str(e)}")

@app.command("/rca")
def root_cause_analysis(ack, command, say):
    ack()
    
    try:
        # Get the command text
        cmd_text = command.get('text', '').strip()
        
        if not cmd_text:
            # Get all pods in all namespaces
            pods = v1.list_pod_for_all_namespaces()
            analysis = []
            
            for pod in pods.items:
                try:
                    # Get pod logs
                    logs = v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=pod.metadata.namespace,
                        tail_lines=50
                    )
                    
                    # Analyze logs
                    pod_analysis = analyze_logs_with_llm(f"Logs from pod {pod.metadata.namespace}/{pod.metadata.name}:\n{logs}")
                    if pod_analysis and pod_analysis.strip():
                        analysis.append(f"=== Analysis for {pod.metadata.namespace}/{pod.metadata.name} ===\n{pod_analysis}\n")
                except Exception as e:
                    logger.error(f"Error analyzing pod {pod.metadata.namespace}/{pod.metadata.name}: {e}")
                    continue
            
            if not analysis:
                say("No pods found to analyze or no valid analysis could be performed")
                return
                
            # Combine all analyses
            full_analysis = "\n".join(analysis)
            if len(full_analysis) > 3000:
                full_analysis = full_analysis[:3000] + "\n... (truncated)"
            
            say(full_analysis)
            
        else:
            # Specific pod analysis
            try:
                namespace, pod = cmd_text.split('/')
                logs = v1.read_namespaced_pod_log(
                    name=pod,
                    namespace=namespace,
                    tail_lines=200
                )
                
                # Analyze logs
                analysis = analyze_logs_with_llm(f"Logs from pod {namespace}/{pod}:\n{logs}")
                
                if not analysis or not analysis.strip():
                    say(f"No valid analysis could be performed for {namespace}/{pod}")
                    return
                
                if len(analysis) > 3000:
                    analysis = analysis[:3000] + "\n... (truncated)"
                
                say(f"=== Analysis for {namespace}/{pod} ===\n{analysis}")
                
            except ValueError:
                say("Usage: /rca [namespace/pod] or just /rca for full cluster analysis")
                return
            except Exception as e:
                say(f"Error getting pod logs: {str(e)}")
                return
        
    except Exception as e:
        logger.error(f"Error in RCA command: {e}")
        say(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        # Start Flask app in a separate thread
        import threading
        threading.Thread(target=flask_app.run, kwargs={'host': '0.0.0.0', 'port': 3000}).start()
        logger.info("Health check endpoint started on port 3000")

        # Start Slack bot
        handler = SocketModeHandler(app=app, app_token=os.environ["SLACK_APP_TOKEN"])
        logger.info("Starting Slack bot...")
        handler.start()
    except Exception as e:
        logger.error(f"Failed to start Slack bot: {e}")
        raise 