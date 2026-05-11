"""
FastAPI service for SHL Assessment Recommender.
Provides /health and /chat endpoints for conversational assessment recommendations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
try:
    from catalog import get_catalog
    from agent import create_agent
    logger.info("Successfully imported catalog and agent modules")
except Exception as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)

# Initialize FastAPI
app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational agent for SHL assessment recommendations",
    version="1.0.0"
)

# Pydantic models for request/response
class Message(BaseModel):
    """Conversation message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat endpoint request."""
    messages: List[Message] = Field(..., description="Conversation history")


class Recommendation(BaseModel):
    """Assessment recommendation."""
    name: str = Field(..., description="Assessment name")
    url: str = Field(..., description="Catalog URL")
    test_type: str = Field(..., description="Single letter test type code (K, P, A, S, etc.)")
    keys: str = Field(default="", description="Assessment keys/categories")
    duration: str = Field(default="-", description="Approximate completion time")
    languages: str = Field(default="-", description="Available languages")


class ChatResponse(BaseModel):
    """Chat endpoint response."""
    reply: str = Field(..., description="Agent response message")
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Assessment recommendations (empty until ready)"
    )
    end_of_conversation: bool = Field(
        default=False,
        description="True when agent considers task complete"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")


# Globals for caching
_catalog_loaded = False


def _ensure_catalog_loaded() -> None:
    """Ensure catalog is loaded on first request."""
    global _catalog_loaded
    if not _catalog_loaded:
        try:
            catalog = get_catalog()
            logger.info(f"Catalog loaded: {len(catalog.get_all_items())} items")
            _catalog_loaded = True
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            raise HTTPException(status_code=500, detail="Catalog loading failed")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        _ensure_catalog_loaded()
        return HealthResponse(status="ok")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for conversational assessment recommendations."""
    try:
        _ensure_catalog_loaded()
        
        # Validate request
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Get the latest user message
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Check turn limit (8 turns max)
        if len(request.messages) > 8:
            return ChatResponse(
                reply="I've reached the conversation limit. Please start a new conversation if you need more assistance.",
                recommendations=[],
                end_of_conversation=True
            )
        
        # Create agent and process message
        agent = create_agent()
        
        # Convert Pydantic messages to dicts for agent
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        response = agent.process_message(user_message, conversation_history)
        
        # Convert recommendations to Pydantic models
        recommendations = [
            Recommendation(
                name=rec['name'],
                url=rec['url'],
                test_type=rec['test_type']
            )
            for rec in response.get('recommendations', [])
        ]
        
        return ChatResponse(
            reply=response['reply'],
            recommendations=recommendations,
            end_of_conversation=response['end_of_conversation']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "service": "SHL Assessment Recommender",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "chat": "POST /chat"
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting SHL Assessment Recommender service...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
