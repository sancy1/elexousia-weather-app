"""
FILE: backend/app/api/routes/chat.py
AI Chat endpoint with SSE streaming
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

from app.agent.weather_agent import get_agent
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    city_context: Optional[str] = None
    unit: str = "C"


# Active streaming sessions (for stop functionality)
_active_sessions: dict = {}


@router.post("")
async def chat(request: ChatRequest):
    """
    Send message to agent, stream response via SSE
    """
    agent = get_agent()
    
    async def event_generator():
        try:
            async for event in agent.run_query(
                message=request.message,
                session_id=request.session_id,
                city_context=request.city_context,
                unit=request.unit
            ):
                # Format as SSE event
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Chat streaming error: {e}")
            error_event = {"type": "error", "detail": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/stop")
async def stop_chat(session_id: Optional[str] = None):
    """
    Cancel current streaming response for session
    """
    if session_id and session_id in _active_sessions:
        del _active_sessions[session_id]
        return {"success": True, "message": "Chat stopped"}
    return {"success": False, "message": "Session not found or already stopped"}
