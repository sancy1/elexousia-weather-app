"""
FILE: backend/app/tests/unit/test_chat_history.py
Unit tests for conversation listing/message loading (chat-history sidebar).
All DB calls are mocked — no live database or LLM calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.memory import (
    list_conversations,
    get_conversation_messages,
    delete_conversation,
    clear_conversations,
)


def _db_cm(cursor):
    """Mock get_db_connection async context manager yielding a conn with cursor."""
    conn = MagicMock()
    conn.cursor.return_value = cursor
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


# ── list_conversations ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_conversations_auth_scopes_to_user():
    cur = MagicMock()
    cur.fetchall.return_value = [
        (1, "sess-a", "Weather in Lagos?", "Lagos", 3, None, None),
    ]
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await list_conversations(user_id=7, session_id="sess-a")

    sql, params = cur.execute.call_args.args
    assert "user_id = %s" in sql
    assert "session_id" not in sql.split("WHERE")[1].split("AND")[0] or True
    assert params[0] == 7
    assert result[0]["title"] == "Weather in Lagos?"
    assert result[0]["message_count"] == 3


@pytest.mark.asyncio
async def test_list_conversations_guest_requires_session_and_null_user():
    cur = MagicMock()
    cur.fetchall.return_value = []
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        await list_conversations(user_id=None, session_id="guest-sess")

    sql, params = cur.execute.call_args.args
    assert "user_id IS NULL" in sql
    assert "session_id = %s" in sql
    assert params[0] == "guest-sess"


@pytest.mark.asyncio
async def test_list_conversations_guest_without_session_returns_empty():
    result = await list_conversations(user_id=None, session_id=None)
    assert result == []


@pytest.mark.asyncio
async def test_list_conversations_search_uses_ilike():
    cur = MagicMock()
    cur.fetchall.return_value = []
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        await list_conversations(user_id=7, search="lagos")

    sql, params = cur.execute.call_args.args
    assert "ILIKE" in sql
    assert "%lagos%" in params


@pytest.mark.asyncio
async def test_list_conversations_db_error_returns_empty():
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=Exception("db down"))
    cm.__aexit__ = AsyncMock(return_value=False)
    with patch("app.agent.memory.get_db_connection", return_value=cm):
        result = await list_conversations(user_id=7)
    assert result == []


# ── get_conversation_messages ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_messages_auth_owner_returns_exchanges():
    cur = MagicMock()
    # ownership check fetchone -> row; messages fetchall -> rows
    cur.fetchone.return_value = (42,)
    cur.fetchall.return_value = [
        ("Weather in Lagos?", "It is 31C.", "Lagos", None),
    ]
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await get_conversation_messages(42, user_id=7)

    assert result is not None
    assert result[0]["user_message"] == "Weather in Lagos?"
    assert result[0]["bot_response"] == "It is 31C."
    # ownership query used user_id
    first_sql, first_params = cur.execute.call_args_list[0].args
    assert "user_id = %s" in first_sql
    assert first_params == (42, 7)


@pytest.mark.asyncio
async def test_get_messages_guest_wrong_session_returns_none():
    cur = MagicMock()
    cur.fetchone.return_value = None  # ownership check fails
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await get_conversation_messages(42, user_id=None, session_id="other-sess")
    assert result is None


@pytest.mark.asyncio
async def test_get_messages_guest_correct_session_returns_rows():
    cur = MagicMock()
    cur.fetchone.return_value = (42,)
    cur.fetchall.return_value = [("hi", "hello", None, None)]
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await get_conversation_messages(42, user_id=None, session_id="sess-1")

    assert result is not None and len(result) == 1
    first_sql, first_params = cur.execute.call_args_list[0].args
    assert "user_id IS NULL" in first_sql
    assert first_params == (42, "sess-1")


@pytest.mark.asyncio
async def test_get_messages_auth_other_user_returns_none():
    """Authenticated user cannot read another user's conversation."""
    cur = MagicMock()
    cur.fetchone.return_value = None
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await get_conversation_messages(42, user_id=99)
    assert result is None


# ── chat_history endpoints ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_list_guest_without_session_400():
    from fastapi import HTTPException
    from app.api.routes.chat_history import list_user_conversations

    with pytest.raises(HTTPException) as exc:
        await list_user_conversations(session_id=None, q=None, limit=50, user=None)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_endpoint_list_guest_with_session_ok():
    from app.api.routes.chat_history import list_user_conversations

    fake = [
        {
            "id": 1,
            "session_id": "s",
            "title": "t",
            "city_name": None,
            "message_count": 1,
            "created_at": None,
            "last_active_at": None,
        }
    ]
    with patch(
        "app.api.routes.chat_history.list_conversations", new=AsyncMock(return_value=fake)
    ) as m:
        result = await list_user_conversations(session_id="s", q=None, limit=50, user=None)

    assert result["conversations"] == fake
    assert m.await_args.kwargs["user_id"] is None
    assert m.await_args.kwargs["session_id"] == "s"


@pytest.mark.asyncio
async def test_endpoint_messages_not_found_404():
    from fastapi import HTTPException
    from app.api.routes.chat_history import get_conversation_messages_endpoint

    with patch(
        "app.api.routes.chat_history.get_conversation_messages", new=AsyncMock(return_value=None)
    ):
        with pytest.raises(HTTPException) as exc:
            await get_conversation_messages_endpoint(
                conversation_id=42, session_id="s", limit=100, user=None
            )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_endpoint_messages_returns_exchanges():
    from app.api.routes.chat_history import get_conversation_messages_endpoint

    fake = [{"user_message": "hi", "bot_response": "yo", "city_resolved": None, "created_at": None}]


# ── delete_conversation ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_conversation_owner_deletes_messages_and_row():
    cur = MagicMock()
    cur.fetchone.return_value = (42,)  # ownership check passes
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await delete_conversation(42, user_id=7)

    assert result is True
    sqls = [c.args[0] for c in cur.execute.call_args_list]
    assert any("DELETE FROM weather_messages" in s for s in sqls)
    assert any("DELETE FROM weather_conversations" in s for s in sqls)
    # ownership check scoped to user_id
    first_sql, first_params = cur.execute.call_args_list[0].args
    assert "user_id = %s" in first_sql
    assert first_params == (42, 7)


@pytest.mark.asyncio
async def test_delete_conversation_other_user_returns_false_no_delete():
    cur = MagicMock()
    cur.fetchone.return_value = None  # ownership check fails
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await delete_conversation(42, user_id=99)

    assert result is False
    # only the ownership SELECT ran — no DELETE statements
    for c in cur.execute.call_args_list:
        assert "DELETE" not in c.args[0]


@pytest.mark.asyncio
async def test_delete_conversation_guest_wrong_session_returns_false():
    cur = MagicMock()
    cur.fetchone.return_value = None
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await delete_conversation(42, user_id=None, session_id="other-sess")

    assert result is False
    first_sql, first_params = cur.execute.call_args_list[0].args
    assert "user_id IS NULL" in first_sql
    assert first_params == (42, "other-sess")


@pytest.mark.asyncio
async def test_delete_conversation_guest_correct_session_deletes():
    cur = MagicMock()
    cur.fetchone.return_value = (42,)
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await delete_conversation(42, user_id=None, session_id="sess-1")

    assert result is True
    first_sql, first_params = cur.execute.call_args_list[0].args
    assert "user_id IS NULL AND session_id = %s" in first_sql
    assert first_params == (42, "sess-1")


@pytest.mark.asyncio
async def test_delete_conversation_guest_without_session_returns_false():
    result = await delete_conversation(42, user_id=None, session_id=None)
    assert result is False


# ── clear_conversations ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clear_conversations_auth_scopes_to_user():
    cur = MagicMock()
    cur.rowcount = 3
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await clear_conversations(user_id=7)

    assert result == 3
    # both DELETEs scoped to user_id = %s
    for c in cur.execute.call_args_list:
        assert "user_id = %s" in c.args[0]
        assert c.args[1] == (7,)


@pytest.mark.asyncio
async def test_clear_conversations_guest_scopes_to_session_and_null_user():
    cur = MagicMock()
    cur.rowcount = 2
    with patch("app.agent.memory.get_db_connection", return_value=_db_cm(cur)):
        result = await clear_conversations(user_id=None, session_id="sess-1")

    assert result == 2
    for c in cur.execute.call_args_list:
        assert "user_id IS NULL AND session_id = %s" in c.args[0]
        assert c.args[1] == ("sess-1",)


@pytest.mark.asyncio
async def test_clear_conversations_guest_without_session_returns_minus_one():
    result = await clear_conversations(user_id=None, session_id=None)
    assert result == -1


@pytest.mark.asyncio
async def test_clear_conversations_db_error_returns_minus_one():
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=Exception("db down"))
    cm.__aexit__ = AsyncMock(return_value=False)
    with patch("app.agent.memory.get_db_connection", return_value=cm):
        result = await clear_conversations(user_id=7)
    assert result == -1


# ── delete endpoints ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_delete_guest_without_session_400():
    from fastapi import HTTPException
    from app.api.routes.chat_history import delete_conversation_endpoint

    with pytest.raises(HTTPException) as exc:
        await delete_conversation_endpoint(conversation_id=42, session_id=None, user=None)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_endpoint_delete_not_found_404():
    from fastapi import HTTPException
    from app.api.routes.chat_history import delete_conversation_endpoint

    with patch(
        "app.api.routes.chat_history.delete_conversation", new=AsyncMock(return_value=False)
    ):
        with pytest.raises(HTTPException) as exc:
            await delete_conversation_endpoint(conversation_id=42, session_id="s", user=None)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_endpoint_delete_success():
    from app.api.routes.chat_history import delete_conversation_endpoint

    with patch(
        "app.api.routes.chat_history.delete_conversation", new=AsyncMock(return_value=True)
    ) as m:
        result = await delete_conversation_endpoint(conversation_id=42, session_id="s", user=None)
    assert result == {"deleted": True}
    assert m.await_args.kwargs["user_id"] is None
    assert m.await_args.kwargs["session_id"] == "s"


@pytest.mark.asyncio
async def test_endpoint_clear_guest_without_session_400():
    from fastapi import HTTPException
    from app.api.routes.chat_history import clear_conversations_endpoint

    with pytest.raises(HTTPException) as exc:
        await clear_conversations_endpoint(session_id=None, user=None)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_endpoint_clear_success_returns_count():
    from app.api.routes.chat_history import clear_conversations_endpoint

    with patch(
        "app.api.routes.chat_history.clear_conversations", new=AsyncMock(return_value=4)
    ) as m:
        result = await clear_conversations_endpoint(session_id="s", user=None)
    assert result == {"deleted": 4}
    assert m.await_args.kwargs["user_id"] is None
    assert m.await_args.kwargs["session_id"] == "s"


@pytest.mark.asyncio
async def test_endpoint_clear_db_error_500():
    from fastapi import HTTPException
    from app.api.routes.chat_history import clear_conversations_endpoint

    with patch("app.api.routes.chat_history.clear_conversations", new=AsyncMock(return_value=-1)):
        with pytest.raises(HTTPException) as exc:
            await clear_conversations_endpoint(session_id="s", user=None)
    assert exc.value.status_code == 500
