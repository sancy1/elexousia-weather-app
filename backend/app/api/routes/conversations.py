"""
FILE: backend/app/api/routes/conversations.py
Conversations and history endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Path, Query
from pydantic import BaseModel
from typing import Optional

from app.infrastructure.repositories.conversation_repository import (
    create_conversation,
    get_conversations,
    get_conversation,
    save_message,
    get_messages,
    update_conversation_title,
    archive_conversation,
    delete_conversation,
    get_conversation_by_session_id
)
from app.api.dependencies import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class CreateConversationRequest(BaseModel):
    session_id: str
    title: Optional[str] = None
    city_name: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None


@router.get("")
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user = Depends(get_current_user)
):
    """
    Get user's conversation list for sidebar (paginated)
    """
    user_id = user.id
    
    try:
        result = await get_conversations(user_id, page, per_page)
        return result
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")


@router.post("")
async def create_new_conversation(body: CreateConversationRequest, user = Depends(get_current_user)):
    """
    Create new conversation, returns session_id
    """
    user_id = user.id
    
    try:
        conversation = await create_conversation(
            user_id=user_id,
            session_id=body.session_id,
            title=body.title,
            city_name=body.city_name
        )
        
        if conversation:
            return conversation
        else:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/{conversation_id}")
async def get_single_conversation(
    conversation_id: int = Path(..., description="Conversation ID"),
    user = Depends(get_current_user)
):
    """
    Get full conversation with all messages
    """
    user_id = user.id
    
    try:
        conversation = await get_conversation(conversation_id, user_id)
        
        if conversation:
            return conversation
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: int = Path(..., description="Conversation ID"),
    body: UpdateConversationRequest = None,
    user = Depends(get_current_user)
):
    """
    Update title or archive a conversation
    """
    user_id = user.id
    
    if body is None:
        body = UpdateConversationRequest()
    
    try:
        if body.title is not None:
            success = await update_conversation_title(conversation_id, user_id, body.title)
            if not success:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        if body.is_archived is not None and body.is_archived:
            success = await archive_conversation(conversation_id, user_id)
            if not success:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to update conversation")


@router.delete("/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int = Path(..., description="Conversation ID"),
    user = Depends(get_current_user)
):
    """
    Permanently delete conversation and all messages
    """
    user_id = user.id
    
    try:
        success = await delete_conversation(conversation_id, user_id)
        
        if success:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int = Path(..., description="Conversation ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    user = Depends(get_current_user)
):
    """
    Returns paginated messages for a conversation
    """
    user_id = user.id
    
    # Verify ownership
    conversation = await get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    try:
        result = await get_messages(conversation_id, page, per_page)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")