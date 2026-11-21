"""
FILE: backend/app/tests/unit/test_memory.py
Unit tests for conversation memory (app.agent.memory) and its wiring in
WeatherAgent.run_query. All LLM and DB calls are mocked — no live Groq calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from app.agent import memory
from app.agent.memory import (
    ensure_conversation,
    load_history,
    save_exchange,
    MESSAGE_CONTENT_LIMIT,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_db_conn(cursor):
    """Build a mock connection usable as `async with get_db_connection()`."""
    conn = MagicMock()
    conn.cursor.return_value = cursor
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _cursor(fetchone=None, fetchall=None):
    cur = MagicMock()
    cur.fetchone.return_value = fetchone
    cur.fetchall.return_value = fetchall or []
    return cur


# ── ensure_conversation ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ensure_conversation_creates_new():
    """First message creates a weather_conversations row."""
    cur = _cursor(fetchone=None)  # SELECT finds nothing
    cur.fetchone.side_effect = [None, (42,)]  # then INSERT ... RETURNING id
    cm = _mock_db_conn(cur)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        conv_id = await ensure_conversation("sess-1", user_id=7, first_message="Weather in Lagos?")

    assert conv_id == 42
    # INSERT was executed with user_id, session_id, title, city_name
    insert_call = cur.execute.call_args_list[-1]
    assert "INSERT INTO weather_conversations" in insert_call.args[0]
    assert insert_call.args[1][0] == 7
    assert insert_call.args[1][1] == "sess-1"


@pytest.mark.asyncio
async def test_ensure_conversation_returns_existing():
    """Existing conversation for the same session+user is reused."""
    cur = _cursor(fetchone=(99,))
    cm = _mock_db_conn(cur)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        conv_id = await ensure_conversation("sess-1", user_id=7, first_message="hi")

    assert conv_id == 99
    # No INSERT should have run
    for call in cur.execute.call_args_list:
        assert "INSERT" not in call.args[0]


@pytest.mark.asyncio
async def test_ensure_conversation_guest_uses_null_user():
    """Guest conversations are scoped with user_id NULL."""
    cur = _cursor(fetchone=None)
    cur.fetchone.side_effect = [None, (5,)]
    cm = _mock_db_conn(cur)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        await ensure_conversation("sess-g", user_id=None, first_message="guest chat")

    select_call = cur.execute.call_args_list[0]
    assert "IS NOT DISTINCT FROM" in select_call.args[0]
    assert select_call.args[1] == ("sess-g", None)


@pytest.mark.asyncio
async def test_ensure_conversation_empty_session_returns_none():
    assert await ensure_conversation("", user_id=1, first_message="hi") is None
    assert await ensure_conversation(None, user_id=1, first_message="hi") is None
    assert await ensure_conversation("   ", user_id=1, first_message="hi") is None


@pytest.mark.asyncio
async def test_ensure_conversation_db_error_returns_none():
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=Exception("db down"))
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        assert await ensure_conversation("sess-1", 1, "hi") is None


# ── save_exchange ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_exchange_inserts_both_messages():
    """Assistant response is persisted together with the user message."""
    cur = _cursor()
    cm = _mock_db_conn(cur)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        ok = await save_exchange(
            session_id="sess-1",
            user_id=7,
            user_message="Weather in Lagos?",
            bot_response="It is 31C and sunny.",
            conversation_id=42,
            city_resolved="Lagos",
        )

    assert ok is True
    insert_call = cur.execute.call_args_list[0]
    assert "INSERT INTO weather_messages" in insert_call.args[0]
    params = insert_call.args[1]
    assert params[0] == "sess-1"
    assert params[1] == "Weather in Lagos?"
    assert params[2] == "It is 31C and sunny."
    assert params[4] == 7
    assert params[5] == 42  # conversation_id ('exchange' role is a SQL literal)
    # conversation counters bumped
    assert any("UPDATE weather_conversations" in c.args[0] for c in cur.execute.call_args_list)


@pytest.mark.asyncio
async def test_save_exchange_db_error_returns_false():
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=Exception("db down"))
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        ok = await save_exchange("sess-1", 1, "hi", "hello")
    assert ok is False


@pytest.mark.asyncio
async def test_save_exchange_truncates_long_content():
    cur = _cursor()
    cm = _mock_db_conn(cur)
    long_text = "x" * (MESSAGE_CONTENT_LIMIT + 500)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        await save_exchange("sess-1", None, long_text, "short")

    params = cur.execute.call_args_list[0].args[1]
    assert len(params[1]) <= MESSAGE_CONTENT_LIMIT


# ── load_history ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_history_returns_message_pairs_chronological():
    """Prior exchanges become HumanMessage/AIMessage pairs, oldest first."""
    # DB returns DESC order (newest first)
    cur = _cursor(
        fetchall=[
            ("second question?", "second answer."),
            ("first question?", "first answer."),
        ]
    )
    cm = _mock_db_conn(cur)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        msgs = await load_history("sess-1", user_id=7)

    assert len(msgs) == 4
    assert isinstance(msgs[0], HumanMessage) and msgs[0].content == "first question?"
    assert isinstance(msgs[1], AIMessage) and msgs[1].content == "first answer."
    assert isinstance(msgs[2], HumanMessage) and msgs[2].content == "second question?"
    assert isinstance(msgs[3], AIMessage) and msgs[3].content == "second answer."

    # Ownership scoping is enforced in SQL
    sql = cur.execute.call_args_list[0].args[0]
    assert "IS NOT DISTINCT FROM" in sql
    assert "JOIN weather_conversations" in sql
    params = cur.execute.call_args_list[0].args[1]
    assert params[0] == "sess-1"
    assert params[1] == 7


@pytest.mark.asyncio
async def test_load_history_guest_scoped_to_null_user():
    cur = _cursor(fetchall=[])
    cm = _mock_db_conn(cur)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        await load_history("sess-g", user_id=None)

    params = cur.execute.call_args_list[0].args[1]
    assert params == ("sess-g", None, memory.HISTORY_EXCHANGE_LIMIT)


@pytest.mark.asyncio
async def test_load_history_empty_session_returns_empty():
    assert await load_history("", user_id=1) == []
    assert await load_history(None, user_id=1) == []


@pytest.mark.asyncio
async def test_load_history_db_error_returns_empty():
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=Exception("db down"))
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        assert await load_history("sess-1", 1) == []


@pytest.mark.asyncio
async def test_load_history_respects_limit():
    cur = _cursor(fetchall=[])
    cm = _mock_db_conn(cur)

    with patch("app.agent.memory.get_db_connection", return_value=cm):
        await load_history("sess-1", 1, limit=3)

    assert cur.execute.call_args_list[0].args[1][2] == 3


# ── WeatherAgent.run_query wiring ─────────────────────────────────────────────


def _make_agent():
    """Build a WeatherAgent without invoking the real LLM graph."""
    from app.agent.weather_agent import WeatherAgent

    agent = WeatherAgent.__new__(WeatherAgent)
    agent.graph = MagicMock()
    return agent


def _fake_result(messages):
    return {"messages": messages}


@pytest.mark.asyncio
async def test_run_query_first_message_creates_and_saves_exchange():
    """First message: no history loaded; exchange persisted after generation."""
    agent = _make_agent()
    agent.graph.ainvoke = AsyncMock(
        return_value=_fake_result([AIMessage(content="It is 31C and sunny in Lagos.")])
    )

    with (
        patch(
            "app.agent.weather_agent.retrieve_city_context",
            new=AsyncMock(return_value=MagicMock(records=[], source="none")),
        ),
        patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
        patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])) as mock_load,
        patch(
            "app.agent.weather_agent.ensure_conversation", new=AsyncMock(return_value=42)
        ) as mock_ensure,
        patch(
            "app.agent.weather_agent.save_exchange", new=AsyncMock(return_value=True)
        ) as mock_save,
    ):
        events = [
            e
            async for e in agent.run_query(
                message="Weather in Lagos?", session_id="sess-1", user_id=7
            )
        ]

    # History was requested for the session
    mock_load.assert_awaited_once_with("sess-1", 7)
    # Conversation ensured and exchange saved with both texts
    mock_ensure.assert_awaited_once()
    save_kwargs = mock_save.await_args.kwargs
    assert save_kwargs["user_message"] == "Weather in Lagos?"
    assert save_kwargs["bot_response"] == "It is 31C and sunny in Lagos."
    assert save_kwargs["conversation_id"] == 42
    # Token + done events emitted
    assert any(e["type"] == "token" for e in events)
    assert events[-1]["type"] == "done"


@pytest.mark.asyncio
async def test_run_query_followup_includes_history_in_ainvoke():
    """Follow-up: prior HumanMessage/AIMessage pairs are passed to the graph."""
    agent = _make_agent()
    history = [
        HumanMessage(content="Weather in Lagos?"),
        AIMessage(content="It is 31C and sunny."),
    ]
    agent.graph.ainvoke = AsyncMock(
        return_value=_fake_result(
            history
            + [
                HumanMessage(content="What about tomorrow?"),
                AIMessage(content="Tomorrow it will rain."),
            ]
        )
    )

    with (
        patch(
            "app.agent.weather_agent.retrieve_city_context",
            new=AsyncMock(return_value=MagicMock(records=[], source="none")),
        ),
        patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
        patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=history)),
        patch("app.agent.weather_agent.ensure_conversation", new=AsyncMock(return_value=42)),
        patch("app.agent.weather_agent.save_exchange", new=AsyncMock(return_value=True)),
    ):
        events = [
            e
            async for e in agent.run_query(
                message="What about tomorrow?", session_id="sess-1", user_id=7
            )
        ]

    # ainvoke received history + new human message
    invoke_messages = agent.graph.ainvoke.await_args.args[0]["messages"]
    assert len(invoke_messages) == 3
    assert isinstance(invoke_messages[0], HumanMessage)
    assert invoke_messages[0].content == "Weather in Lagos?"
    assert isinstance(invoke_messages[1], AIMessage)
    assert invoke_messages[1].content == "It is 31C and sunny."
    assert isinstance(invoke_messages[2], HumanMessage)
    assert "What about tomorrow?" in invoke_messages[2].content

    # History AI message must NOT be re-streamed as a token
    token_contents = [e["content"] for e in events if e["type"] == "token"]
    assert "It is 31C and sunny." not in token_contents
    assert "Tomorrow it will rain." in token_contents


@pytest.mark.asyncio
async def test_run_query_guest_passes_none_user_id():
    """Guests get memory scoped with user_id=None."""
    agent = _make_agent()
    agent.graph.ainvoke = AsyncMock(return_value=_fake_result([AIMessage(content="ok")]))

    with (
        patch(
            "app.agent.weather_agent.retrieve_city_context",
            new=AsyncMock(return_value=MagicMock(records=[], source="none")),
        ),
        patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
        patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])) as mock_load,
        patch("app.agent.weather_agent.ensure_conversation", new=AsyncMock(return_value=None)),
        patch("app.agent.weather_agent.save_exchange", new=AsyncMock(return_value=True)),
    ):
        _ = [e async for e in agent.run_query(message="hi", session_id="sess-g", user_id=None)]

    mock_load.assert_awaited_once_with("sess-g", None)


@pytest.mark.asyncio
async def test_run_query_no_session_skips_memory():
    """Missing session_id: memory functions are never called."""
    agent = _make_agent()
    agent.graph.ainvoke = AsyncMock(return_value=_fake_result([AIMessage(content="ok")]))

    with (
        patch(
            "app.agent.weather_agent.retrieve_city_context",
            new=AsyncMock(return_value=MagicMock(records=[], source="none")),
        ),
        patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
        patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])) as mock_load,
        patch("app.agent.weather_agent.ensure_conversation", new=AsyncMock()) as mock_ensure,
        patch("app.agent.weather_agent.save_exchange", new=AsyncMock()) as mock_save,
    ):
        _ = [e async for e in agent.run_query(message="hi", session_id=None)]

    mock_load.assert_not_awaited()
    mock_ensure.assert_not_awaited()
    mock_save.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_query_memory_failure_still_streams_response():
    """DB failure in memory layer degrades gracefully — chat still works.

    memory.py functions catch DB errors internally and return
    [] / None / False (verified in their own tests); here we simulate that
    fail-soft contract end-to-end through run_query.
    """
    agent = _make_agent()
    agent.graph.ainvoke = AsyncMock(return_value=_fake_result([AIMessage(content="still works")]))

    with (
        patch(
            "app.agent.weather_agent.retrieve_city_context",
            new=AsyncMock(return_value=MagicMock(records=[], source="none")),
        ),
        patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
        patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
        patch("app.agent.weather_agent.ensure_conversation", new=AsyncMock(return_value=None)),
        patch("app.agent.weather_agent.save_exchange", new=AsyncMock(return_value=False)),
    ):
        events = [e async for e in agent.run_query(message="hi", session_id="sess-1", user_id=1)]

    assert any(e["type"] == "token" and e["content"] == "still works" for e in events)
    assert events[-1]["type"] == "done"
