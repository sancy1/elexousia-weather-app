"""
FILE: backend/app/tests/unit/test_retrieval.py
Unit tests for RAG context retrieval (app.agent.retrieval)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.agent.retrieval import (
    RetrievedContext,
    retrieve_city_context,
    format_retrieved_context,
)
from app.agent.weather_agent import WeatherAgent, _enrich_message


# ── Helpers ──────────────────────────────────────────────────────────────────


class _FakeCursor:
    def __init__(self, fetchall_rows=None, fetchone_row=None):
        self._fetchall_rows = fetchall_rows or []
        self._fetchone_row = fetchone_row
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self._fetchall_rows

    def fetchone(self):
        return self._fetchone_row

    def close(self):
        pass


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class _FakeCM:
    """Async context manager mimicking get_db_connection()."""

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        return False


def _vector_row(
    city_id=1,
    name="Lagos",
    country="Nigeria",
    cc="NG",
    lat=6.5244,
    lon=3.3792,
    tz="Africa/Lagos",
    pop=15400000,
    capital=True,
    state=None,
    content="Lagos is in Nigeria.",
    similarity=0.83,
):
    return (city_id, name, country, cc, lat, lon, tz, pop, capital, state, content, similarity)


# ── Retrieval: vector search ─────────────────────────────────────────────────


class TestVectorRetrieval:
    @pytest.mark.asyncio
    async def test_vector_search_produces_records(self):
        cursor = _FakeCursor(fetchall_rows=[_vector_row()])
        conn = _FakeConn(cursor)

        with (
            patch("app.agent.retrieval.settings") as mock_settings,
            patch("app.agent.retrieval._embed_query", return_value=[0.1] * 1024),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            mock_settings.RAG_VECTOR_SEARCH_ENABLED = True
            result = await retrieve_city_context("weather in Lagos")

        assert result.source == "vector_search"
        assert len(result.records) == 1
        rec = result.records[0]
        assert rec["city_name"] == "Lagos"
        assert rec["country_code"] == "NG"
        assert rec["population"] == 15400000
        assert rec["is_capital"] is True
        assert rec["similarity"] == pytest.approx(0.83)
        assert "content_snippet" in rec

    @pytest.mark.asyncio
    async def test_vector_search_filters_low_similarity(self):
        cursor = _FakeCursor(fetchall_rows=[_vector_row(similarity=0.30)])
        conn = _FakeConn(cursor)

        with (
            patch("app.agent.retrieval._embed_query", return_value=[0.1] * 1024),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            result = await retrieve_city_context("zzz unrelated")

        # Below threshold → falls through to DB fallback; with no DB mock it
        # resolves to none (resolve_city_from_db will hit real DB? No — it is
        # patched below via _database_fallback path). Patch it explicitly.
        assert result.source in ("none", "database_fallback", "alias_fallback")

    @pytest.mark.asyncio
    async def test_vector_search_dedupes_cities(self):
        rows = [
            _vector_row(city_id=1, similarity=0.90),
            _vector_row(city_id=1, similarity=0.85),  # same city, lower sim
            _vector_row(city_id=2, name="Abuja", similarity=0.70),
        ]
        cursor = _FakeCursor(fetchall_rows=rows)
        conn = _FakeConn(cursor)

        with (
            patch("app.agent.retrieval.settings") as mock_settings,
            patch("app.agent.retrieval._embed_query", return_value=[0.1] * 1024),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            mock_settings.RAG_VECTOR_SEARCH_ENABLED = True
            result = await retrieve_city_context("lagos")

        assert result.source == "vector_search"
        assert len(result.records) == 2
        assert result.records[0]["city_name"] == "Lagos"
        assert result.records[1]["city_name"] == "Abuja"


# ── Retrieval: fallbacks ─────────────────────────────────────────────────────


class TestRetrievalFallbacks:
    @pytest.mark.asyncio
    async def test_fallback_to_database_when_embedding_fails(self):
        """Ollama embed failure must not crash; DB fallback still yields context."""
        cities_row = (
            "Lagos",
            "Nigeria",
            "NG",
            6.5244,
            3.3792,
            "Africa/Lagos",
            15400000,
            True,
            None,
        )
        cursor = _FakeCursor(fetchone_row=cities_row)
        conn = _FakeConn(cursor)

        with (
            patch("app.agent.retrieval._embed_query", side_effect=Exception("ollama down")),
            patch(
                "app.agent.retrieval.resolve_city_from_db",
                new=AsyncMock(
                    return_value={
                        "city_id": 1,
                        "city_name": "Lagos",
                        "country_name": "Nigeria",
                        "country_code": "NG",
                        "latitude": 6.5,
                        "longitude": 3.3,
                        "timezone": "Africa/Lagos",
                        "resolution": "db",
                    }
                ),
            ),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            result = await retrieve_city_context("Lagos")

        assert result.source == "database_fallback"
        assert len(result.records) == 1
        assert result.records[0]["city_name"] == "Lagos"
        assert result.records[0]["is_capital"] is True

    @pytest.mark.asyncio
    async def test_alias_fallback(self):
        alias_row = (
            1,
            "New York",
            "United States",
            "US",
            40.71,
            -74.0,
            "America/New_York",
            8336000,
            False,
            "New York",
            "nyc",
        )
        cursor = _FakeCursor(fetchone_row=alias_row)
        conn = _FakeConn(cursor)

        with (
            patch("app.agent.retrieval._embed_query", side_effect=Exception("down")),
            patch("app.agent.retrieval.resolve_city_from_db", new=AsyncMock(return_value=None)),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            result = await retrieve_city_context("nyc")

        assert result.source == "alias_fallback"
        assert result.records[0]["matched_alias"] == "nyc"

    @pytest.mark.asyncio
    async def test_empty_query_returns_none(self):
        result = await retrieve_city_context("")
        assert result.source == "none"
        assert result.records == []

        result = await retrieve_city_context("   ")
        assert result.source == "none"

    @pytest.mark.asyncio
    async def test_all_sources_fail_returns_none(self):
        with (
            patch("app.agent.retrieval._embed_query", side_effect=Exception("down")),
            patch("app.agent.retrieval.resolve_city_from_db", new=AsyncMock(return_value=None)),
            patch("app.agent.retrieval.get_db_connection", side_effect=Exception("db down")),
        ):
            result = await retrieve_city_context("atlantis")

        assert result.source == "none"
        assert result.records == []


# ── Retrieval: RAG_VECTOR_SEARCH_ENABLED flag ────────────────────────────────


class TestVectorSearchFlag:
    @pytest.mark.asyncio
    async def test_flag_disabled_skips_ollama_and_uses_db(self):
        """When disabled, _embed_query must never be called; DB fallback used."""
        cities_row = (
            "Lagos",
            "Nigeria",
            "NG",
            6.5244,
            3.3792,
            "Africa/Lagos",
            15400000,
            True,
            None,
        )
        cursor = _FakeCursor(fetchone_row=cities_row)
        conn = _FakeConn(cursor)
        embed_mock = MagicMock(side_effect=AssertionError("Ollama must not be called"))

        async def fake_resolve(candidate):
            if candidate.lower() == "lagos":
                return {
                    "city_id": 1,
                    "city_name": "Lagos",
                    "country_name": "Nigeria",
                    "country_code": "NG",
                    "latitude": 6.5,
                    "longitude": 3.3,
                    "timezone": "Africa/Lagos",
                    "resolution": "db",
                }
            return None

        with (
            patch("app.agent.retrieval.settings") as mock_settings,
            patch("app.agent.retrieval._embed_query", embed_mock),
            patch(
                "app.agent.retrieval.resolve_city_from_db", new=AsyncMock(side_effect=fake_resolve)
            ),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            mock_settings.RAG_VECTOR_SEARCH_ENABLED = False
            result = await retrieve_city_context("What should I wear in Lagos tomorrow?")

        embed_mock.assert_not_called()
        assert result.source == "database_fallback"
        assert result.records[0]["city_name"] == "Lagos"

    @pytest.mark.asyncio
    async def test_flag_enabled_attempts_vector_first(self):
        cursor = _FakeCursor(fetchall_rows=[_vector_row()])
        conn = _FakeConn(cursor)

        with (
            patch("app.agent.retrieval.settings") as mock_settings,
            patch("app.agent.retrieval._embed_query", return_value=[0.1] * 1024),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            mock_settings.RAG_VECTOR_SEARCH_ENABLED = True
            result = await retrieve_city_context("weather in Lagos")

        assert result.source == "vector_search"


# ── Retrieval: natural-language queries resolve to real cities ───────────────


class TestNaturalLanguageQueries:
    @pytest.mark.asyncio
    async def test_wear_in_lagos_tomorrow_resolves_lagos(self):
        """Regression: 'What should I wear in Lagos tomorrow?' must not return none."""
        cities_row = (
            "Lagos",
            "Nigeria",
            "NG",
            6.5244,
            3.3792,
            "Africa/Lagos",
            15400000,
            True,
            None,
        )
        cursor = _FakeCursor(fetchone_row=cities_row)
        conn = _FakeConn(cursor)

        async def fake_resolve(candidate):
            if candidate.strip().lower() == "lagos":
                return {
                    "city_id": 1,
                    "city_name": "Lagos",
                    "country_name": "Nigeria",
                    "country_code": "NG",
                    "latitude": 6.5,
                    "longitude": 3.3,
                    "timezone": "Africa/Lagos",
                    "resolution": "db",
                }
            return None

        with (
            patch("app.agent.retrieval._embed_query", side_effect=Exception("down")),
            patch(
                "app.agent.retrieval.resolve_city_from_db", new=AsyncMock(side_effect=fake_resolve)
            ),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            result = await retrieve_city_context("What should I wear in Lagos tomorrow?")

        assert result.source == "database_fallback"
        assert result.records[0]["city_name"] == "Lagos"
        assert result.records[0]["country_code"] == "NG"

    @pytest.mark.asyncio
    async def test_compare_query_still_resolves_first_city(self):
        """'Compare New York and Toronto' should resolve at least one city."""
        cities_row = (
            "New York",
            "United States",
            "US",
            40.71,
            -74.0,
            "America/New_York",
            8336000,
            False,
            "New York",
        )
        cursor = _FakeCursor(fetchone_row=cities_row)
        conn = _FakeConn(cursor)

        async def fake_resolve(candidate):
            if "new york" in candidate.lower():
                return {
                    "city_id": 2,
                    "city_name": "New York",
                    "country_name": "United States",
                    "country_code": "US",
                    "latitude": 40.7,
                    "longitude": -74.0,
                    "timezone": "America/New_York",
                    "resolution": "db",
                }
            return None

        with (
            patch("app.agent.retrieval._embed_query", side_effect=Exception("down")),
            patch(
                "app.agent.retrieval.resolve_city_from_db", new=AsyncMock(side_effect=fake_resolve)
            ),
            patch("app.agent.retrieval.get_db_connection", return_value=_FakeCM(conn)),
        ):
            result = await retrieve_city_context("Compare the weather in New York and Toronto")

        assert result.source in ("database_fallback", "alias_fallback")
        assert result.records


# ── Formatting ───────────────────────────────────────────────────────────────


class TestFormatRetrievedContext:
    def test_format_empty(self):
        assert format_retrieved_context(RetrievedContext()) == ""

    def test_format_includes_key_fields(self):
        ctx = RetrievedContext(
            records=[
                {
                    "city_name": "Lagos",
                    "country_name": "Nigeria",
                    "country_code": "NG",
                    "latitude": 6.52,
                    "longitude": 3.38,
                    "timezone": "Africa/Lagos",
                    "population": 15400000,
                    "is_capital": True,
                    "similarity": 0.83,
                    "content_snippet": "Lagos is in Nigeria.",
                }
            ],
            source="vector_search",
        )
        block = format_retrieved_context(ctx)
        assert "[Retrieved context" in block
        assert "NOT live weather" in block
        assert "Lagos, Nigeria (NG)" in block
        assert "Africa/Lagos" in block
        assert "capital: yes" in block
        assert "similarity: 0.83" in block


# ── Prompt enrichment ────────────────────────────────────────────────────────


class TestEnrichMessage:
    def test_context_block_included(self):
        block = "[Retrieved context — test]\n- Lagos, Nigeria (NG)"
        out = _enrich_message("weather tomorrow?", None, "C", block)
        assert "[Retrieved context" in out
        assert "Lagos, Nigeria" in out
        assert out.endswith("weather tomorrow?")

    def test_backward_compatible_without_context(self):
        out = _enrich_message("hi", "Paris", "F")
        assert "[Current city context: Paris]" in out
        assert "Fahrenheit" in out
        assert "Retrieved context" not in out


# ── Agent integration: context reaches graph.ainvoke ─────────────────────────


class TestAgentRAGIntegration:
    @pytest.mark.asyncio
    async def test_retrieved_context_event_and_prompt(self):
        agent = WeatherAgent.__new__(WeatherAgent)
        fake_graph = MagicMock()
        fake_graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="It is sunny.")]}
        )
        agent.graph = fake_graph

        ctx = RetrievedContext(
            records=[
                {
                    "city_name": "Lagos",
                    "country_name": "Nigeria",
                    "country_code": "NG",
                    "latitude": 6.5,
                    "longitude": 3.3,
                    "timezone": "Africa/Lagos",
                    "population": 15400000,
                    "is_capital": True,
                    "similarity": 0.9,
                }
            ],
            source="vector_search",
        )

        with patch(
            "app.agent.weather_agent.retrieve_city_context", new=AsyncMock(return_value=ctx)
        ):
            events = [e async for e in agent.run_query("weather in Lagos")]

        types = [e["type"] for e in events]
        assert "retrieved_context" in types
        assert "token" in types
        assert "done" in types

        rc_event = next(e for e in events if e["type"] == "retrieved_context")
        assert rc_event["retrieval_source"] == "vector_search"
        assert rc_event["cities"][0]["city_name"] == "Lagos"

        # The HumanMessage passed to ainvoke must contain the context block
        call_args = fake_graph.ainvoke.call_args[0][0]
        human_msg = call_args["messages"][0]
        assert "[Retrieved context" in human_msg.content
        assert "Lagos, Nigeria (NG)" in human_msg.content
        assert "NOT live weather" in human_msg.content

    @pytest.mark.asyncio
    async def test_no_context_still_completes(self):
        agent = WeatherAgent.__new__(WeatherAgent)
        fake_graph = MagicMock()
        fake_graph.ainvoke = AsyncMock(return_value={"messages": [AIMessage(content="Hello")]})
        agent.graph = fake_graph

        with patch(
            "app.agent.weather_agent.retrieve_city_context",
            new=AsyncMock(return_value=RetrievedContext(source="none")),
        ):
            events = [e async for e in agent.run_query("hi")]

        types = [e["type"] for e in events]
        assert "retrieved_context" in types
        assert "done" in types
        call_args = fake_graph.ainvoke.call_args[0][0]
        assert "Retrieved context" not in call_args["messages"][0].content
