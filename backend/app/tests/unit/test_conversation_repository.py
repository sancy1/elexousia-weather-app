"""
FILE: backend/app/tests/unit/test_conversation_repository.py
Unit tests for conversation repository
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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


class TestConversationRepository:
    """Test conversation repository functions"""
    
    @pytest.mark.asyncio
    async def test_create_conversation_success(self):
        """Test successfully creating a conversation"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 1, "session-123", "Weather Chat", "Lagos", 0, False, None, None)
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await create_conversation(
                user_id=1,
                session_id="session-123",
                title="Weather Chat",
                city_name="Lagos"
            )
            
            assert result is not None
            assert result["session_id"] == "session-123"
            assert result["title"] == "Weather Chat"
    
    @pytest.mark.asyncio
    async def test_get_conversations(self):
        """Test getting conversations for a user"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # Total count
        mock_cursor.fetchall.return_value = [
            (1, 1, "session-123", "Lagos weather", "Lagos", 4, False, None, None),
            (2, 1, "session-456", "London forecast", "London", 2, False, None, None)
        ]
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await get_conversations(user_id=1, page=1, per_page=20)
            
            assert result["total"] == 2
            assert len(result["conversations"]) == 2
            assert result["conversations"][0]["title"] == "Lagos weather"
    
    @pytest.mark.asyncio
    async def test_get_conversation_by_id(self):
        """Test getting a single conversation by ID"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 1, "session-123", "Weather Chat", "Lagos", 4, False, None, None)
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await get_conversation(conversation_id=1, user_id=1)
            
            assert result is not None
            assert result["id"] == 1
    
    @pytest.mark.asyncio
    async def test_save_message(self):
        """Test saving a message to a conversation"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 1, "user", "What's the weather?", "session-123", "Lagos", None)
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await save_message(
                conversation_id=1,
                role="user",
                content="What's the weather?",
                session_id="session-123",
                city_context="Lagos"
            )
            
            assert result is not None
            assert result["role"] == "user"
            assert result["content"] == "What's the weather?"
    
    @pytest.mark.asyncio
    async def test_get_messages(self):
        """Test getting messages for a conversation"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # Total count
        mock_cursor.fetchall.return_value = [
            (1, 1, "user", "What's the weather?", "session-123", "Lagos", None),
            (2, 1, "assistant", "It's sunny in Lagos", "session-123", "Lagos", None)
        ]
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await get_messages(conversation_id=1, page=1, per_page=50)
            
            assert result["total"] == 2
            assert len(result["messages"]) == 2
            assert result["messages"][0]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_update_conversation_title(self):
        """Test updating conversation title"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await update_conversation_title(conversation_id=1, user_id=1, title="New Title")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_archive_conversation(self):
        """Test archiving a conversation"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await archive_conversation(conversation_id=1, user_id=1)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self):
        """Test deleting a conversation"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await delete_conversation(conversation_id=1, user_id=1)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_conversation_by_session_id(self):
        """Test getting a conversation by session ID"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 1, "session-123", "Weather Chat", "Lagos", 4, False, None, None)
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.conversation_repository.get_db_connection', return_value=mock_conn):
            result = await get_conversation_by_session_id("session-123")
            
            assert result is not None
            assert result["session_id"] == "session-123"
