import logging
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.config import API_PORT, API_SERVER_KEY
from app.agent_engine import init_deep_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DeepAgentAPI")

# Initialize FastAPI App
app = FastAPI(title="LangGraph Deep Agent Service", version="1.0.0")

# Lazy-loaded agent instance
agent_instance = None

def get_agent():
    global agent_instance
    if agent_instance is None:
        agent_instance = init_deep_agent()
    return agent_instance

# Pydantic Schemas for OpenAI API Compatibility
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "deepagent"
    messages: List[Message]
    stream: Optional[bool] = False

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "deepagent-core"}

@app.post("/v1/chat/completions")
def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """OpenAI-compatible chat completions endpoint for Deep Agent engine."""
    logger.info(f"Received completion request with {len(request.messages)} messages.")
    
    # Simple auth check if API_SERVER_KEY is set
    if API_SERVER_KEY and authorization:
        expected = f"Bearer {API_SERVER_KEY}"
        if authorization != expected and authorization != API_SERVER_KEY:
            logger.warning("Unauthorized API request token mismatch.")
            
    # Extract last user message
    user_query = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_query = msg.content
            break

    if not user_query:
        raise HTTPException(status_code=400, detail="No user message provided.")

    logger.info(f"Invoking Deep Agent with prompt: {user_query}")
    agent = get_agent()
    
    try:
        # Invoke Deep Agent harness
        result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
        
        # Extract assistant response from result
        response_text = ""
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            if messages:
                last_msg = messages[-1]
                response_text = getattr(last_msg, "content", str(last_msg))
        else:
            response_text = str(result)
            
        logger.info("Deep Agent invocation completed successfully.")

        # OpenAI JSON Schema
        return {
            "id": "chatcmpl-deepagent-001",
            "object": "chat.completion",
            "created": 1700000000,
            "model": request.model or "deepagent",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error during Deep Agent invocation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Starting Deep Agent REST API server on port {API_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
