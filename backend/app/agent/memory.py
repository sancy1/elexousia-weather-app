"""
FILE: backend/app/agent/memory.py
Persistent conversation memory for the weather agent.

Uses the existing public.weather_conversations and public.weather_messages
tables (one weather_messages row per exchange: user_message + bot_response).

Access rules (strict):
  - Authenticated user: only conversations where user_id = current user id
  - Guest:              only conversations where user_id IS NULL
  - session_id alone is never treated as authorization.

All functions fail soft: database errors are logged and return empty/None so
chat always proceeds without memory.
"""

from typing import Any, List, Optional

from langchain_core.messages import AIMessage, HumanMessage

from app.infrastructure.database.session import get_db_connection
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Last N exchanges loaded into the prompt (each exchange = 1 user + 1 assistant msg)
HISTORY_EXCHANGE_LIMIT = 10
# Per-message content cap to bound prompt size
MESSAGE_CONTENT_LIMIT = 1000
# Title stored on first exchange
TITLE_MAX_LENGTH = 80


def _truncate(text: str, limit: int = MESSAGE_CONTENT_LIMIT) -> str:
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


async def ensure_conversation(
    session_id: str,
    user_id: Optional[int],
    first_message: str,
    city_name: Optional[str] = None,
) -> Optional[int]:
    """
    Get or create a weather_conversations row for this session.

    Returns the conversation id, or None on failure / missing session_id.
    """
    if not session_id or not session_id.strip():
        return None
    session_id = session_id.strip()

    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            # NULL-safe user match: authenticated -> own rows only,
            # guest -> user_id IS NULL rows only.
            cursor.execute(
                """
                SELECT id FROM weather_conversations
                WHERE session_id = %s AND user_id IS NOT DISTINCT FROM %s
                LIMIT 1;
                """,
                (session_id, user_id),
            )
            row = cursor.fetchone()
            if row:
                cursor.close()
                return row[0]

            title = _truncate(first_message, TITLE_MAX_LENGTH) or "Weather chat"
            cursor.execute(
                """
                INSERT INTO weather_conversations
                    (user_id, session_id, title, city_name, message_count,
                     is_archived, created_at, last_active_at)
                VALUES (%s, %s, %s, %s, 0, FALSE, NOW(), NOW())
                RETURNING id;
                """,
                (user_id, session_id, title, city_name),
            )
            conv_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            return conv_id
    except Exception as e:
        logger.error(f"ensure_conversation failed: {e}")
        return None


async def save_exchange(
    session_id: str,
    user_id: Optional[int],
    user_message: str,
    bot_response: str,
    conversation_id: Optional[int] = None,
    city_resolved: Optional[str] = None,
) -> bool:
    """
    Persist one exchange (user message + assistant response) to
    weather_messages and bump the conversation counters.

    Returns True on success, False on any failure (never raises).
    """
    if not session_id or not session_id.strip():
        return False
    session_id = session_id.strip()

    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO weather_messages
                    (session_id, user_message, bot_response, city_resolved,
                     user_id, role, conversation_id, created_at)
                VALUES (%s, %s, %s, %s, %s, 'exchange', %s, NOW());
                """,
                (
                    session_id,
                    _truncate(user_message),
                    _truncate(bot_response),
                    city_resolved,
                    user_id,
                    conversation_id,
                ),
            )
            if conversation_id:
                cursor.execute(
                    """
                    UPDATE weather_conversations
                    SET message_count = message_count + 1,
                        last_active_at = NOW()
                    WHERE id = %s;
                    """,
                    (conversation_id,),
                )
            conn.commit()
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"save_exchange failed: {e}")
        return False


async def load_history(
    session_id: str,
    user_id: Optional[int],
    limit: int = HISTORY_EXCHANGE_LIMIT,
) -> List[Any]:
    """
    Load recent exchanges as LangChain HumanMessage/AIMessage objects,
    oldest first, ready to prepend to the agent's message list.

    Access is scoped through weather_conversations ownership:
      authenticated -> user_id = current user
      guest         -> user_id IS NULL
    Returns [] on missing session, no conversation, or any DB error.
    """
    if not session_id or not session_id.strip():
        return []
    session_id = session_id.strip()

    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT m.user_message, m.bot_response
                FROM weather_messages m
                JOIN weather_conversations c ON c.id = m.conversation_id
                WHERE m.session_id = %s
                  AND c.user_id IS NOT DISTINCT FROM %s
                ORDER BY m.created_at DESC
                LIMIT %s;
                """,
                (session_id, user_id, limit),
            )
            rows = cursor.fetchall()
            cursor.close()
    except Exception as e:
        logger.error(f"load_history failed: {e}")
        return []

    messages: List[Any] = []
    for user_msg, bot_msg in reversed(rows):  # DESC -> chronological
        if user_msg:
            messages.append(HumanMessage(content=_truncate(user_msg)))
        if bot_msg:
            messages.append(AIMessage(content=_truncate(bot_msg)))
    return messages


async def list_conversations(
    user_id: Optional[int],
    session_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
) -> List[dict]:
    """
    List conversations visible to the caller.

    Authenticated user -> all conversations owned by that user.
    Guest              -> only conversations for this session_id with
                          user_id IS NULL (session_id alone never authorizes
                          access to another user's rows).

    Returns [] on DB error. Never raises.
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            if user_id is not None:
                sql = """
                    SELECT id, session_id, title, city_name, message_count,
                           created_at, last_active_at
                    FROM weather_conversations
                    WHERE user_id = %s AND is_archived = FALSE
                """
                params: list = [user_id]
            else:
                if not session_id or not session_id.strip():
                    return []
                sql = """
                    SELECT id, session_id, title, city_name, message_count,
                           created_at, last_active_at
                    FROM weather_conversations
                    WHERE session_id = %s AND user_id IS NULL AND is_archived = FALSE
                """
                params = [session_id.strip()]

            if search and search.strip():
                sql += " AND title ILIKE %s"
                params.append(f"%{search.strip()}%")

            sql += " ORDER BY last_active_at DESC NULLS LAST LIMIT %s"
            params.append(limit)

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            cursor.close()
    except Exception as e:
        logger.error(f"list_conversations failed: {e}")
        return []

    return [
        {
            "id": r[0],
            "session_id": r[1],
            "title": r[2] or "Weather chat",
            "city_name": r[3],
            "message_count": r[4] or 0,
            "created_at": r[5].isoformat() if r[5] else None,
            "last_active_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]


async def get_conversation_messages(
    conversation_id: int,
    user_id: Optional[int],
    session_id: Optional[str] = None,
    limit: int = 100,
) -> Optional[List[dict]]:
    """
    Load exchanges for one conversation after verifying ownership.

    Ownership check mirrors list_conversations:
      authenticated -> user_id = caller
      guest         -> user_id IS NULL AND session_id = caller's session

    Returns None when the conversation does not exist or is not accessible
    (callers should map this to 404 — never leak existence).
    Returns [] when accessible but empty. Never raises on DB error (returns None).
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            if user_id is not None:
                cursor.execute(
                    "SELECT id FROM weather_conversations WHERE id = %s AND user_id = %s;",
                    (conversation_id, user_id),
                )
            else:
                if not session_id or not session_id.strip():
                    return None
                cursor.execute(
                    """
                    SELECT id FROM weather_conversations
                    WHERE id = %s AND user_id IS NULL AND session_id = %s;
                    """,
                    (conversation_id, session_id.strip()),
                )
            if not cursor.fetchone():
                cursor.close()
                return None

            cursor.execute(
                """
                SELECT user_message, bot_response, city_resolved, created_at
                FROM weather_messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                LIMIT %s;
                """,
                (conversation_id, limit),
            )
            rows = cursor.fetchall()
            cursor.close()
    except Exception as e:
        logger.error(f"get_conversation_messages failed: {e}")
        return None

    return [
        {
            "user_message": r[0],
            "bot_response": r[1],
            "city_resolved": r[2],
            "created_at": r[3].isoformat() if r[3] else None,
        }
        for r in rows
    ]


def _ownership_clause(user_id: Optional[int], session_id: Optional[str]):
    """
    Return (sql_fragment, params) enforcing the same ownership rules as
    list_conversations / get_conversation_messages:
      authenticated -> user_id = caller
      guest         -> user_id IS NULL AND session_id = caller's session
    Returns (None, None) when a guest session_id is missing.
    """
    if user_id is not None:
        return "user_id = %s", [user_id]
    if not session_id or not session_id.strip():
        return None, None
    return "user_id IS NULL AND session_id = %s", [session_id.strip()]


async def delete_conversation(
    conversation_id: int,
    user_id: Optional[int],
    session_id: Optional[str] = None,
) -> bool:
    """
    Permanently delete one conversation and its messages.

    Ownership is verified with the same rules as get_conversation_messages —
    a caller can only delete conversations they could read. Returns False
    when the conversation does not exist or is not accessible (no existence
    leak). Never raises on DB error.
    """
    clause, params = _ownership_clause(user_id, session_id)
    if clause is None:
        return False

    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id FROM weather_conversations WHERE id = %s AND {clause};",
                (conversation_id, *params),
            )
            if not cursor.fetchone():
                cursor.close()
                return False

            cursor.execute(
                "DELETE FROM weather_messages WHERE conversation_id = %s;",
                (conversation_id,),
            )
            cursor.execute(
                "DELETE FROM weather_conversations WHERE id = %s;",
                (conversation_id,),
            )
            conn.commit()
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"delete_conversation failed: {e}")
        return False


async def clear_conversations(
    user_id: Optional[int],
    session_id: Optional[str] = None,
) -> int:
    """
    Permanently delete ALL conversations (and their messages) visible to the
    caller: every conversation owned by an authenticated user, or every
    guest conversation for the exact session_id.

    Returns the number of conversations deleted, or -1 on DB error / missing
    guest session. Never raises.
    """
    clause, params = _ownership_clause(user_id, session_id)
    if clause is None:
        return -1

    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM weather_messages
                WHERE conversation_id IN (
                    SELECT id FROM weather_conversations WHERE {clause}
                );
                """,
                tuple(params),
            )
            cursor.execute(
                f"DELETE FROM weather_conversations WHERE {clause};",
                tuple(params),
            )
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            return deleted
    except Exception as e:
        logger.error(f"clear_conversations failed: {e}")
        return -1
