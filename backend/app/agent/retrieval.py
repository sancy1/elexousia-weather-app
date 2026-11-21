"""
FILE: backend/app/agent/retrieval.py
Retrieval-Augmented Generation (RAG) context retrieval for the weather agent.

Retrieves stored city/entity knowledge from PostgreSQL + pgvector BEFORE the
LLM generates a response, so the retrieved context can be injected into the
prompt. This is entity/context retrieval only — live weather data still comes
exclusively from WeatherAPI via the agent tools.

Retrieval sources (in priority order):
  1. vector_search      — pgvector cosine similarity over city_embeddings
  2. database_fallback  — SQL resolve_city() (exact/alias/full-text)
  3. alias_fallback     — direct city_aliases lookup
  4. none               — no context found; agent proceeds without it
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.agent.tools.city_resolver import (
    EMBED_MODEL,
    QUERY_PREFIX,
    detect_region_from_query,
    normalize_city_name,
    resolve_city_from_db,
)
from app.infrastructure.database.session import get_db_connection
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Minimum cosine similarity for a vector hit to count as relevant context.
VECTOR_SIMILARITY_THRESHOLD = 0.50
DEFAULT_TOP_K = 3


@dataclass
class RetrievedContext:
    """Structured result of a retrieval step."""

    records: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "none"  # vector_search | database_fallback | alias_fallback | none
    query: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.records


def _embed_query(query_text: str) -> List[float]:
    """Synchronous Ollama embedding call (run via asyncio.to_thread)."""
    import ollama as ollama_client

    response = ollama_client.embed(
        model=EMBED_MODEL,
        input=f"{QUERY_PREFIX}{query_text}",
    )
    return response["embeddings"][0]


def _clean_query(text: str) -> str:
    """Strip weather/advice-related words, mirroring resolve_city()'s cleaning."""
    cleaned = re.sub(
        r"\b(weather|forecast|temperature|rain|sunny|cloudy|today|tomorrow|"
        r"this week|in|at|for|the|whats|what is|tell me|is it|will it|"
        r"should i|i am going to|travelling to|wear|wearing|clothing|dress|"
        r"jacket|umbrella|sunscreen|advice|recommend|recommendation|"
        r"compare|between|and|my|me|i|should|what|whats)\b",
        "",
        text.lower(),
    ).strip()
    return cleaned or text.lower().strip()


def _candidate_queries(query: str) -> List[str]:
    """
    Build ordered candidate strings for DB/alias resolution.

    A raw user query like "What should I wear in Lagos tomorrow?" will not
    match resolve_city() directly — candidates progressively strip noise so
    the city token ("lagos") is eventually tried on its own.
    """
    candidates: List[str] = []
    seen = set()

    def add(value: Optional[str]) -> None:
        v = (value or "").strip(" ,?.!")
        if v and v.lower() not in seen and len(v) >= 2:
            seen.add(v.lower())
            candidates.append(v)

    add(query)
    normalized = normalize_city_name(query)
    add(normalized)
    add(_clean_query(normalized))
    add(_clean_query(query))
    # Last-token fallback: "wear lagos" -> "lagos"
    for candidate in list(candidates):
        tokens = candidate.split()
        if len(tokens) > 1:
            add(tokens[-1])
    return candidates


def _row_to_record(
    row: tuple,
    similarity: Optional[float] = None,
    snippet: Optional[str] = None,
    alias: Optional[str] = None,
) -> Dict[str, Any]:
    """Normalize a cities-row tuple into a context record."""
    record: Dict[str, Any] = {
        "city_name": row[1],
        "country_name": row[2],
        "country_code": row[3],
        "latitude": float(row[4]) if row[4] is not None else None,
        "longitude": float(row[5]) if row[5] is not None else None,
        "timezone": row[6],
        "population": row[7],
        "is_capital": bool(row[8]) if row[8] is not None else False,
        "state_province": row[9],
    }
    if similarity is not None:
        record["similarity"] = round(float(similarity), 4)
    if snippet:
        record["content_snippet"] = snippet[:200]
    if alias:
        record["matched_alias"] = alias
    return record


async def _vector_search(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    """Top-k semantic city lookup via pgvector. Returns [] on any failure."""
    try:
        query_vec = await asyncio.to_thread(_embed_query, query_text)
    except Exception as e:
        logger.warning(f"RAG embedding failed, skipping vector retrieval: {e}")
        return []

    region_codes = detect_region_from_query(query_text)

    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            base_sql = """
                SELECT c.id, c.city_name, c.country_name, c.country_code,
                       c.latitude, c.longitude, c.timezone,
                       c.population, c.is_capital, c.state_province,
                       e.content,
                       1 - (e.embedding <=> %s::vector) AS similarity
                FROM city_embeddings e JOIN cities c ON c.id = e.city_id
                WHERE e.embedding IS NOT NULL
            """
            params: list = [json.dumps(query_vec)]
            if region_codes:
                base_sql += " AND c.country_code = ANY(%s)"
                params.append(region_codes)
            base_sql += " ORDER BY e.embedding <=> %s::vector LIMIT %s"
            params.extend([json.dumps(query_vec), top_k])

            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
            cursor.close()
    except Exception as e:
        logger.error(f"RAG vector search error: {e}")
        return []

    # Dedupe by city (keep highest similarity), enforce threshold
    seen = set()
    records = []
    for row in rows:
        city_id = row[0]
        if city_id in seen:
            continue
        seen.add(city_id)
        similarity = float(row[11])
        if similarity < VECTOR_SIMILARITY_THRESHOLD:
            continue
        records.append(_row_to_record(row[:10], similarity=similarity, snippet=row[10]))
    return records


async def _database_fallback(query_text: str) -> Optional[Dict[str, Any]]:
    """Resolve via SQL resolve_city() then fetch full city metadata."""
    resolved = None
    for candidate in _candidate_queries(query_text):
        resolved = await resolve_city_from_db(candidate)
        if resolved and resolved.get("city_id") is not None:
            break
    if not resolved or resolved.get("city_id") is None:
        return None
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT city_name, country_name, country_code, latitude, longitude,
                       timezone, population, is_capital, state_province
                FROM cities WHERE id = %s LIMIT 1;
                """,
                (resolved["city_id"],),
            )
            row = cursor.fetchone()
            cursor.close()
        if row:
            # cities-only row: indices shift — build record manually
            return {
                "city_name": row[0],
                "country_name": row[1],
                "country_code": row[2],
                "latitude": float(row[3]) if row[3] is not None else None,
                "longitude": float(row[4]) if row[4] is not None else None,
                "timezone": row[5],
                "population": row[6],
                "is_capital": bool(row[7]) if row[7] is not None else False,
                "state_province": row[8],
            }
    except Exception as e:
        logger.error(f"RAG database fallback error: {e}")
    # Minimal record from resolver output if full row unavailable
    return {
        "city_name": resolved.get("city_name"),
        "country_name": resolved.get("country_name"),
        "country_code": resolved.get("country_code"),
        "latitude": resolved.get("latitude"),
        "longitude": resolved.get("longitude"),
        "timezone": resolved.get("timezone"),
    }


async def _alias_fallback(query_text: str) -> Optional[Dict[str, Any]]:
    """Direct city_aliases lookup for abbreviation/nickname matches."""
    candidates: set = set()
    for candidate in _candidate_queries(query_text):
        candidates.add(candidate.lower())
        candidates.add(_clean_query(candidate))
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.id, c.city_name, c.country_name, c.country_code,
                       c.latitude, c.longitude, c.timezone,
                       c.population, c.is_capital, c.state_province,
                       a.alias
                FROM city_aliases a JOIN cities c ON c.id = a.city_id
                WHERE lower(a.alias) = ANY(%s)
                LIMIT 1;
                """,
                (list(candidates),),
            )
            row = cursor.fetchone()
            cursor.close()
        if row:
            record = _row_to_record(row[:10], alias=row[10])
            return record
    except Exception as e:
        logger.error(f"RAG alias fallback error: {e}")
    return None


async def retrieve_city_context(query: str, top_k: int = DEFAULT_TOP_K) -> RetrievedContext:
    """
    Retrieve relevant city/entity context for a user query.

    Never raises — returns RetrievedContext(source="none") on any failure so
    the chat request always proceeds.
    """
    result = RetrievedContext(query=query)
    if not query or not query.strip():
        return result

    # 1. Vector search (primary) — only when enabled (local dev / Ollama).
    #    Production sets RAG_VECTOR_SEARCH_ENABLED=false to skip Ollama
    #    entirely and rely on PostgreSQL city/alias resolution.
    if getattr(settings, "RAG_VECTOR_SEARCH_ENABLED", True):
        records = await _vector_search(query.strip(), top_k)
        if records:
            result.records = records
            result.source = "vector_search"
            return result

    # 2. Database fallback (exact/alias/full-text via SQL resolve_city)
    record = await _database_fallback(query.strip())
    if record:
        result.records = [record]
        result.source = "database_fallback"
        return result

    # 3. Alias fallback
    record = await _alias_fallback(query.strip())
    if record:
        result.records = [record]
        result.source = "alias_fallback"
        return result

    result.source = "none"
    return result


def format_retrieved_context(context: RetrievedContext) -> str:
    """
    Render retrieved records as a compact prompt block.

    The block is explicitly labeled as background knowledge — NOT live weather.
    """
    if context.is_empty:
        return ""

    lines = ["[Retrieved context — city/entity background knowledge, NOT live weather data]"]
    for rec in context.records:
        parts = [f"- {rec.get('city_name')}, {rec.get('country_name')} ({rec.get('country_code')})"]
        details = []
        if rec.get("state_province"):
            details.append(f"region: {rec['state_province']}")
        if rec.get("latitude") is not None and rec.get("longitude") is not None:
            details.append(f"coords: {rec['latitude']:.2f}, {rec['longitude']:.2f}")
        if rec.get("timezone"):
            details.append(f"tz: {rec['timezone']}")
        if rec.get("population"):
            details.append(f"pop: {rec['population']:,}")
        if rec.get("is_capital"):
            details.append("capital: yes")
        if rec.get("matched_alias"):
            details.append(f"alias: {rec['matched_alias']}")
        if rec.get("similarity") is not None:
            details.append(f"similarity: {rec['similarity']}")
        if details:
            parts.append(" — " + ", ".join(details))
        if rec.get("content_snippet"):
            parts.append(f" | {rec['content_snippet']}")
        lines.append("".join(parts))

    return "\n".join(lines)
