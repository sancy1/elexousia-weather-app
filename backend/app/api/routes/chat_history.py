"""
FILE: backend/app/api/routes/chat_history.py
Chat-history endpoints for the swappable sidebar panel.

Access rules (strict, same as conversation memory):
  - Authenticated user -> only their own conversations (user_id = caller)
  - Guest              -> only conversations with user_id IS NULL for the
                          provided session_id
  - session_id alone never authorizes access to another user's data.
"""

from fastapi import APIRouter, Depends, Query, HTTPException

from app.agent.memory import (
    list_conversations,
    get_conversation_messages,
    delete_conversation,
    clear_conversations,
)
from app.api.dependencies import get_optional_user

router = APIRouter(prefix="/chat", tags=["Chat History"])


@router.get("/conversations")
async def list_user_conversations(
    session_id: str | None = Query(None, description="Guest session id"),
    q: str | None = Query(None, description="Case-insensitive title search"),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_optional_user),
):
    """
    List conversations for the current user (auth) or guest session.

    Guests must supply session_id; authenticated users see all of their
    conversations regardless of session.
    """
    user_id = user.id if user else None
    if user_id is None and not session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required for guest chat history",
        )

    conversations = await list_conversations(
        user_id=user_id,
        session_id=session_id,
        search=q,
        limit=limit,
    )
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages_endpoint(
    conversation_id: int,
    session_id: str | None = Query(None, description="Guest session id"),
    limit: int = Query(100, ge=1, le=200),
    user=Depends(get_optional_user),
):
    """
    Load exchanges for one conversation after ownership verification.
    Returns 404 for missing OR inaccessible conversations (no existence leak).
    """
    user_id = user.id if user else None
    if user_id is None and not session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required for guest chat history",
        )

    messages = await get_conversation_messages(
        conversation_id=conversation_id,
        user_id=user_id,
        session_id=session_id,
        limit=limit,
    )
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": messages}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int,
    session_id: str | None = Query(None, description="Guest session id"),
    user=Depends(get_optional_user),
):
    """
    Permanently delete one conversation and its messages.
    Ownership rules identical to message loading — 404 for missing OR
    inaccessible conversations (no existence leak).
    """
    user_id = user.id if user else None
    if user_id is None and not session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required for guest chat history",
        )

    deleted = await delete_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        session_id=session_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}


@router.delete("/conversations")
async def clear_conversations_endpoint(
    session_id: str | None = Query(None, description="Guest session id"),
    user=Depends(get_optional_user),
):
    """
    Permanently delete ALL conversations visible to the caller:
    every conversation owned by an authenticated user, or every guest
    conversation for the exact session_id. Other users'/guests' data is
    never touched.
    """
    user_id = user.id if user else None
    if user_id is None and not session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required for guest chat history",
        )

    deleted = await clear_conversations(user_id=user_id, session_id=session_id)
    if deleted < 0:
        raise HTTPException(status_code=500, detail="Failed to clear history")
    return {"deleted": deleted}
