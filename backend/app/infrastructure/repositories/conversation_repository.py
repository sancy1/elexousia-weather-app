"""
FILE: backend/app/infrastructure/repositories/conversation_repository.py
Repository for conversation and message operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.infrastructure.database.session import get_db_connection
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def create_conversation(
    user_id: int,
    session_id: str,
    title: Optional[str] = None,
    city_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new conversation
    
    Args:
        user_id: User ID
        session_id: Session identifier
        title: Optional title (auto-generated from first message if not provided)
        city_name: Optional city context
        
    Returns:
        Conversation dict or None if failed
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations 
                (user_id, session_id, title, city_name, is_archived)
                VALUES (%s, %s, %s, %s, FALSE)
                RETURNING id, user_id, session_id, title, city_name, 
                          message_count, is_archived, created_at, last_active_at
            """, (user_id, session_id, title, city_name))
            
            row = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "title": row[3],
                    "city_name": row[4],
                    "message_count": row[5],
                    "is_archived": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "last_active_at": row[8].isoformat() if row[8] else None
                }
            return None
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        return None


async def get_conversations(
    user_id: int,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """
    Get paginated list of conversations for a user
    
    Args:
        user_id: User ID
        page: Page number
        per_page: Items per page
        
    Returns:
        Dict with conversations list, total, page, per_page
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute(
                "SELECT COUNT(*) FROM conversations WHERE user_id = %s AND is_archived = FALSE",
                (user_id,)
            )
            total = cursor.fetchone()[0]
            
            # Get paginated conversations
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT id, user_id, session_id, title, city_name, 
                       message_count, is_archived, created_at, last_active_at
                FROM conversations
                WHERE user_id = %s AND is_archived = FALSE
                ORDER BY last_active_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, per_page, offset))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "title": row[3],
                    "city_name": row[4],
                    "message_count": row[5],
                    "is_archived": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "last_active_at": row[8].isoformat() if row[8] else None
                })
            
            cursor.close()
            
            return {
                "conversations": conversations,
                "total": total,
                "page": page,
                "per_page": per_page
            }
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        return {"conversations": [], "total": 0, "page": page, "per_page": per_page}


async def get_conversation(conversation_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single conversation with ownership check
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        
    Returns:
        Conversation dict or None
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, session_id, title, city_name, 
                       message_count, is_archived, created_at, last_active_at
                FROM conversations
                WHERE id = %s AND user_id = %s
                LIMIT 1
            """, (conversation_id, user_id))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "title": row[3],
                    "city_name": row[4],
                    "message_count": row[5],
                    "is_archived": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "last_active_at": row[8].isoformat() if row[8] else None
                }
            return None
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        return None


async def save_message(
    conversation_id: int,
    role: str,
    content: str,
    session_id: str,
    city_context: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Save a message to a conversation
    
    Args:
        conversation_id: Conversation ID
        role: Message role (user, assistant, system)
        content: Message content
        session_id: Session identifier
        city_context: Optional city context
        
    Returns:
        Message dict or None if failed
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert message
            cursor.execute("""
                INSERT INTO weather_messages 
                (conversation_id, role, content, session_id, city_context)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, conversation_id, role, content, session_id, 
                          city_context, created_at
            """, (conversation_id, role, content, session_id, city_context))
            
            # Update conversation message count and last_active_at
            cursor.execute("""
                UPDATE conversations
                SET message_count = message_count + 1,
                    last_active_at = NOW()
                WHERE id = %s
            """, (conversation_id,))
            
            row = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            if row:
                return {
                    "id": row[0],
                    "conversation_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "session_id": row[4],
                    "city_context": row[5],
                    "created_at": row[6].isoformat() if row[6] else None
                }
            return None
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        return None


async def get_messages(
    conversation_id: int,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    """
    Get paginated messages for a conversation
    
    Args:
        conversation_id: Conversation ID
        page: Page number
        per_page: Items per page
        
    Returns:
        Dict with messages list, total, page, per_page
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute(
                "SELECT COUNT(*) FROM weather_messages WHERE conversation_id = %s",
                (conversation_id,)
            )
            total = cursor.fetchone()[0]
            
            # Get paginated messages
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT id, conversation_id, role, content, session_id, 
                       city_context, created_at
                FROM weather_messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                LIMIT %s OFFSET %s
            """, (conversation_id, per_page, offset))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "conversation_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "session_id": row[4],
                    "city_context": row[5],
                    "created_at": row[6].isoformat() if row[6] else None
                })
            
            cursor.close()
            
            return {
                "messages": messages,
                "total": total,
                "page": page,
                "per_page": per_page
            }
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        return {"messages": [], "total": 0, "page": page, "per_page": per_page}


async def update_conversation_title(
    conversation_id: int,
    user_id: int,
    title: str
) -> bool:
    """
    Update conversation title
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for ownership check)
        title: New title
        
    Returns:
        True if updated, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET title = %s WHERE id = %s AND user_id = %s",
                (title, conversation_id, user_id)
            )
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
    except Exception as e:
        logger.error(f"Failed to update conversation title: {e}")
        return False


async def archive_conversation(conversation_id: int, user_id: int) -> bool:
    """
    Archive a conversation (soft delete)
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for ownership check)
        
    Returns:
        True if archived, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET is_archived = TRUE WHERE id = %s AND user_id = %s",
                (conversation_id, user_id)
            )
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
    except Exception as e:
        logger.error(f"Failed to archive conversation: {e}")
        return False


async def delete_conversation(conversation_id: int, user_id: int) -> bool:
    """
    Delete a conversation and all messages (hard delete)
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for ownership check)
        
    Returns:
        True if deleted, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Messages will be cascade deleted by foreign key
            cursor.execute(
                "DELETE FROM conversations WHERE id = %s AND user_id = %s",
                (conversation_id, user_id)
            )
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        return False


async def get_conversation_by_session_id(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a conversation by session ID
    
    Args:
        session_id: Session identifier
        
    Returns:
        Conversation dict or None
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, session_id, title, city_name, 
                       message_count, is_archived, created_at, last_active_at
                FROM conversations
                WHERE session_id = %s
                LIMIT 1
            """, (session_id,))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "title": row[3],
                    "city_name": row[4],
                    "message_count": row[5],
                    "is_archived": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "last_active_at": row[8].isoformat() if row[8] else None
                }
            return None
    except Exception as e:
        logger.error(f"Failed to get conversation by session: {e}")
        return None