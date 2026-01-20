from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import logging
import json
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "API_KEY": "your_API_KEY",
    "PROJECT_ID": "your_PROJECT_ID",
    "DEPLOYMENT_ID": "your_DEPLOYMENT_ID",
    "REGION": "us-south",
    "API_VERSION": "2021-05-01"
}

app = FastAPI()

# Data Models
class ChatMessage(BaseModel):
    message: str
    stream: bool = False  # Added streaming option

class ChatResponse(BaseModel):
    response: str
    status: str

class HealthResponse(BaseModel):
    status: str
    api_ready: bool

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint URLs
TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
BASE_ENDPOINT = f"https://{CONFIG['REGION']}.ml.cloud.ibm.com/ml/v4/deployments/{CONFIG['DEPLOYMENT_ID']}"
REGULAR_ENDPOINT = f"{BASE_ENDPOINT}/ai_service?version={CONFIG['API_VERSION']}"
STREAMING_ENDPOINT = f"{BASE_ENDPOINT}/ai_service_stream?version={CONFIG['API_VERSION']}"

# Token cache with expiration tracking
token_cache = {
    "token": None,
    "expires_at": 0
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def get_ibm_token():
    """Get or refresh IBM Cloud IAM token with caching"""
    try:
        # Return cached token if still valid
        if token_cache["token"] and token_cache["expires_at"] > time.time():
            return token_cache["token"]
            
        response = requests.post(
            TOKEN_URL,
            data={
                "apikey": CONFIG["API_KEY"],
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            },
            timeout=10
        )
        response.raise_for_status()
        
        token_data = response.json()
        token_cache["token"] = token_data["access_token"]
        # Set expiration to 1 hour (typical token lifetime is 1 hour)
        token_cache["expires_at"] = time.time() + 3600
        
        return token_cache["token"]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Token request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected token error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

def get_watsonx_payload(message: str):
    """Generate properly formatted payload"""
    return {
        "messages": [{
            "content": message,
            "role": "user"
        }],
        "project_id": CONFIG["PROJECT_ID"],
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }
    }

def format_response(data: dict) -> str:
    """Extract and format the response text"""
    try:
        if "choices" in data and data["choices"]:
            return data["choices"][0].get("message", {}).get("content", "No response content")
        return str(data)
    except Exception:
        return "Received response but couldn't parse it"

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test authentication
        token = get_ibm_token()
        return {
            "status": "healthy",
            "api_ready": bool(token)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "api_ready": False
        }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint with complete error handling"""
    try:
        # Validate input
        if not message.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Get authentication token
        try:
            token = get_ibm_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

        # Prepare request
        payload = get_watsonx_payload(message.message)
        endpoint = STREAMING_ENDPOINT if message.stream else REGULAR_ENDPOINT
        logger.info(f"Sending request to: {endpoint}")

        # Make API call
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 401:
                # Token might be expired, clear cache and retry once
                token_cache["token"] = None
                token = get_ibm_token()
                headers["Authorization"] = f"Bearer {token}"
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30
                )

            response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            error_detail = f"HTTP Error: {e.response.status_code}"
            if e.response.text:
                try:
                    error_data = e.response.json()
                    error_detail += f" - {error_data.get('errors', [{}])[0].get('message', 'Unknown error')}"
                except ValueError:
                    error_detail += f" - {e.response.text}"
            
            logger.error(f"API request failed: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_detail
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable"
            )

        # Process response
        try:
            data = response.json()
            logger.debug(f"Raw response: {json.dumps(data, indent=2)}")
            
            formatted_response = format_response(data)
            
            return ChatResponse(
                response=formatted_response,
                status="success"
            )
            
        except ValueError as e:
            logger.error(f"Invalid JSON response: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from service"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Watsonx Chat API")
    logger.info(f"Regular endpoint: {REGULAR_ENDPOINT}")
    logger.info(f"Streaming endpoint: {STREAMING_ENDPOINT}")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)