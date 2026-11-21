"""
FILE: backend/app/tests/unit/test_streaming.py
Unit tests for WeatherAgent.run_query SSE streaming.
Fully mocked — no live LLM, Groq, or DB calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.weather_agent import WeatherAgent


def make_agent(result_messages=None, ainvoke_side_effect=None):
    """Build a WeatherAgent with a mocked graph (no LLM init)."""
    agent = WeatherAgent.__new__(WeatherAgent)
    graph = MagicMock()
    if ainvoke_side_effect is not None:
        graph.ainvoke = AsyncMock(side_effect=ainvoke_side_effect)
    else:
        graph.ainvoke = AsyncMock(return_value={"messages": result_messages or []})
    agent.graph = graph
    return agent


RETRIEVED = MagicMock(source="none", records=[])


async def collect(agent, **kwargs):
    events = []
    async for event in agent.run_query(message="hi", **kwargs):
        events.append(event)
    return events


class TestStreaming:
    @pytest.mark.asyncio
    async def test_tokens_stream_in_order(self):
        """Token events arrive in message order"""
        msgs = [
            HumanMessage(content="hi"),
            AIMessage(content="Hello "),
            AIMessage(content="there!"),
        ]
        agent = make_agent(result_messages=msgs)

        with (
            patch(
                "app.agent.weather_agent.retrieve_city_context",
                new=AsyncMock(return_value=RETRIEVED),
            ),
            patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
            patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
        ):
            events = await collect(agent, session_id=None)

        tokens = [e["content"] for e in events if e["type"] == "token"]
        assert tokens == ["Hello ", "there!"]
        assert events[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_history_not_restreamed(self):
        """Prior assistant messages before the last HumanMessage are not streamed"""
        msgs = [
            HumanMessage(content="old question"),
            AIMessage(content="OLD ANSWER SHOULD NOT STREAM"),
            HumanMessage(content="new question"),
            AIMessage(content="new answer"),
        ]
        agent = make_agent(result_messages=msgs)

        with (
            patch(
                "app.agent.weather_agent.retrieve_city_context",
                new=AsyncMock(return_value=RETRIEVED),
            ),
            patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
            patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
        ):
            events = await collect(agent, session_id=None)

        tokens = [e["content"] for e in events if e["type"] == "token"]
        assert tokens == ["new answer"]
        assert "OLD ANSWER SHOULD NOT STREAM" not in "".join(tokens)

    @pytest.mark.asyncio
    async def test_exchange_persisted_after_completion(self):
        """save_exchange is called with the full assembled response"""
        msgs = [HumanMessage(content="hi"), AIMessage(content="part1 "), AIMessage(content="part2")]
        agent = make_agent(result_messages=msgs)

        with (
            patch(
                "app.agent.weather_agent.retrieve_city_context",
                new=AsyncMock(return_value=RETRIEVED),
            ),
            patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
            patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
            patch("app.agent.weather_agent.ensure_conversation", new=AsyncMock(return_value=7)),
            patch("app.agent.weather_agent.save_exchange", new=AsyncMock()) as mock_save,
        ):
            events = await collect(agent, session_id="sess-1", user_id=3)

        assert events[-1]["type"] == "done"
        mock_save.assert_awaited_once()
        kwargs = mock_save.await_args.kwargs
        assert kwargs["bot_response"] == "part1 part2"
        assert kwargs["user_message"] == "hi"
        assert kwargs["conversation_id"] == 7

    @pytest.mark.asyncio
    async def test_error_is_sanitized(self):
        """Internal exception details never reach the client"""
        agent = make_agent(ainvoke_side_effect=RuntimeError("groq api key sk-abc123 failed"))

        with (
            patch(
                "app.agent.weather_agent.retrieve_city_context",
                new=AsyncMock(return_value=RETRIEVED),
            ),
            patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
            patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
        ):
            events = await collect(agent, session_id=None)

        errors = [e for e in events if e["type"] == "error"]
        assert len(errors) == 1
        assert "sk-abc123" not in errors[0]["detail"]
        assert "groq" not in errors[0]["detail"].lower()
        assert "try again" in errors[0]["detail"].lower()

    @pytest.mark.asyncio
    async def test_resolved_city_from_tool_call(self):
        """resolved_city event emitted from tool call args (incl. clothing tool)"""
        tool_call = {
            "name": "get_clothing_advice",
            "args": {"city": "Lagos"},
            "id": "call_1",
            "type": "tool_call",
        }
        msgs = [
            HumanMessage(content="what to wear?"),
            AIMessage(content="", tool_calls=[tool_call]),
            AIMessage(content="Wear light clothing."),
        ]
        agent = make_agent(result_messages=msgs)

        with (
            patch(
                "app.agent.weather_agent.retrieve_city_context",
                new=AsyncMock(return_value=RETRIEVED),
            ),
            patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
            patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
        ):
            events = await collect(agent, session_id=None)

        resolved = [e for e in events if e["type"] == "resolved_city"]
        assert resolved and resolved[0]["city"] == "Lagos"

    @pytest.mark.asyncio
    async def test_gemini_list_content_streamed(self):
        """List-format content (Gemini thought parts) yields only text parts"""
        msgs = [
            HumanMessage(content="hi"),
            AIMessage(
                content=[
                    {"type": "thought", "text": "internal reasoning"},
                    {"type": "text", "text": "visible answer"},
                ]
            ),
        ]
        agent = make_agent(result_messages=msgs)

        with (
            patch(
                "app.agent.weather_agent.retrieve_city_context",
                new=AsyncMock(return_value=RETRIEVED),
            ),
            patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
            patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
        ):
            events = await collect(agent, session_id=None)

        tokens = [e["content"] for e in events if e["type"] == "token"]
        assert tokens == ["visible answer"]
        assert "internal reasoning" not in "".join(tokens)

    @pytest.mark.asyncio
    async def test_no_persistence_without_session(self):
        """No session_id -> no memory writes"""
        msgs = [HumanMessage(content="hi"), AIMessage(content="hello")]
        agent = make_agent(result_messages=msgs)

        with (
            patch(
                "app.agent.weather_agent.retrieve_city_context",
                new=AsyncMock(return_value=RETRIEVED),
            ),
            patch("app.agent.weather_agent.format_retrieved_context", return_value=""),
            patch("app.agent.weather_agent.load_history", new=AsyncMock(return_value=[])),
            patch("app.agent.weather_agent.ensure_conversation", new=AsyncMock()) as mock_conv,
            patch("app.agent.weather_agent.save_exchange", new=AsyncMock()) as mock_save,
        ):
            await collect(agent, session_id=None)

        mock_conv.assert_not_awaited()
        mock_save.assert_not_awaited()
