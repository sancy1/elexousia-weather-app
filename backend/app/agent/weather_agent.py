# """
# FILE: backend/app/agent/weather_agent.py
# Core weather agent runner using LangGraph
# """

# from typing import Dict, Any, Optional, AsyncIterator
# import json
# from langgraph.prebuilt import create_react_agent
# from langchain_core.messages import HumanMessage, AIMessage

# from app.agent.prompts import SYSTEM_PROMPT
# from app.agent.llm_provider import get_llm
# from app.agent.tools.weather_tools import get_current_weather, get_weather_forecast, compare_weather
# from app.agent.tools.city_resolver import resolve_city
# from app.core.logging_config import get_logger

# logger = get_logger(__name__)


# class WeatherAgent:
#     """Weather agent powered by LangGraph"""

#     def __init__(self):
#         self.llm = get_llm()
#         self.graph = self._build_graph()

#     def _build_graph(self):
#         """Build the LangGraph for the weather agent"""
#         tools = [get_current_weather, get_weather_forecast, compare_weather]

#         # Bind tools to the LLM (required for Groq)
#         llm_with_tools = self.llm.bind_tools(tools)

#         return create_react_agent(model=llm_with_tools, tools=tools, prompt=SYSTEM_PROMPT)

#     async def run_query(
#         self,
#         message: str,
#         session_id: Optional[str] = None,
#         city_context: Optional[str] = None,
#         unit: str = "C"
#     ) -> AsyncIterator[Dict[str, Any]]:
#         """
#         Run a weather query with streaming support

#         Args:
#             message: User's message
#             session_id: Session identifier for conversation history
#             city_context: Current city context
#             unit: Temperature unit (C or F)

#         Yields:
#             Dict with SSE event data
#         """
#         yield {"type": "start", "session_id": session_id}

#         try:
#             # Run the graph with async invocation
#             result = await self.graph.ainvoke({"messages": [HumanMessage(content=message)]})

#             # Stream the final response and extract resolved city
#             resolved_city = None
#             for msg in result["messages"]:
#                 if isinstance(msg, AIMessage):
#                     if isinstance(msg.content, str):
#                         yield {"type": "token", "content": msg.content}
#                     # Check tool calls for resolved city
#                     if hasattr(msg, 'tool_calls') and msg.tool_calls:
#                         for tool_call in msg.tool_calls:
#                             if tool_call.get('name') in ['get_current_weather', 'get_weather_forecast', 'compare_weather']:
#                                 # Try to extract city from tool arguments
#                                 args = tool_call.get('args', {})
#                                 if 'city' in args:
#                                     resolved_city = args['city']

#             # Send resolved city if found
#             if resolved_city:
#                 yield {"type": "resolved_city", "city": resolved_city}

#             yield {"type": "done"}

#         except Exception as e:
#             logger.error(f"Agent execution error: {e}")
#             yield {"type": "error", "detail": str(e)}


# # Singleton instance
# _agent_instance: Optional[WeatherAgent] = None


# def get_agent() -> WeatherAgent:
#     """Get or create the agent singleton"""
#     global _agent_instance
#     if _agent_instance is None:
#         _agent_instance = WeatherAgent()
#     return _agent_instance


"""
FILE: backend/app/agent/weather_agent.py
Core weather agent runner using LangGraph

Change from original:
  - Import get_llm_with_tools instead of get_llm
  - Use get_llm_with_tools(tools) in _build_graph() so that Gemini
    thinking models receive the thought_signature generation config
    AND the tool binding in a single consistent call.
  - Ollama and Groq are unaffected — get_llm_with_tools() falls back
    to the standard bind_tools() path for those providers.
"""

from typing import Dict, Any, Optional, AsyncIterator
import json
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.prompts import SYSTEM_PROMPT

# ── CHANGED: import get_llm_with_tools instead of get_llm ────────────────────
from app.agent.llm_provider import get_llm_with_tools

from app.agent.tools.weather_tools import (
    get_current_weather,
    get_weather_forecast,
    compare_weather,
    get_clothing_advice,
)
from app.agent.tools.city_resolver import resolve_city
from app.agent.retrieval import retrieve_city_context, format_retrieved_context, RetrievedContext
from app.agent.memory import ensure_conversation, load_history, save_exchange
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class WeatherAgent:
    """Weather agent powered by LangGraph"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the LangGraph for the weather agent."""
        tools = [get_current_weather, get_weather_forecast, compare_weather, get_clothing_advice]

        # ── CHANGED ───────────────────────────────────────────────────────────
        # get_llm_with_tools() handles:
        #   • Ollama / Groq  → get_llm().bind_tools(tools)  (unchanged)
        #   • Gemini thinking models → bind_tools with include_thoughts=True
        #     and tool_config AUTO so thought_signature is returned and
        #     echoed correctly on every subsequent tool-result turn.
        llm_with_tools = get_llm_with_tools(tools)
        # ─────────────────────────────────────────────────────────────────────

        return create_react_agent(
            model=llm_with_tools,
            tools=tools,
            prompt=SYSTEM_PROMPT,
        )

    async def run_query(
        self,
        message: str,
        session_id: Optional[str] = None,
        city_context: Optional[str] = None,
        unit: str = "C",
        user_id: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run a weather query with streaming support.

        Args:
            message:      User's message
            session_id:   Session identifier for conversation memory
            city_context: Current city context (prepended to message if provided)
            unit:         Temperature unit ('C' or 'F')
            user_id:      Authenticated user id (None for guests)

        Yields:
            Dict with SSE event data
        """
        yield {"type": "start", "session_id": session_id}

        conversation_id: Optional[int] = None
        assistant_response_parts: list[str] = []

        try:
            # ── RAG: retrieve stored city/entity context BEFORE generation ──
            # Vector search over city_embeddings (+ DB/alias fallbacks) produces
            # background knowledge injected into the prompt. Live weather still
            # comes only from WeatherAPI via the agent tools.
            retrieved: RetrievedContext = await retrieve_city_context(message)
            context_block = format_retrieved_context(retrieved)

            yield {
                "type": "retrieved_context",
                "retrieval_source": retrieved.source,
                "cities": [
                    {
                        "city_name": r.get("city_name"),
                        "country_name": r.get("country_name"),
                        "country_code": r.get("country_code"),
                        "similarity": r.get("similarity"),
                    }
                    for r in retrieved.records
                ],
            }

            # Optionally inject city, unit, and retrieved context into the
            # human message so the agent doesn't have to ask for clarification.
            enriched_message = _enrich_message(message, city_context, unit, context_block)

            # ── Conversation memory: load prior exchanges for this session ──
            # Scoped by session_id AND user_id (guests -> user_id IS NULL).
            history = await load_history(session_id, user_id) if session_id else []
            messages = history + [HumanMessage(content=enriched_message)]

            result = await self.graph.ainvoke({"messages": messages})

            resolved_city: Optional[str] = None

            # result["messages"] includes loaded history — only process the
            # tail after the last HumanMessage (the current turn) so prior
            # assistant replies are not re-streamed as tokens.
            result_messages = result.get("messages", [])
            last_human_idx = max(
                (i for i, m in enumerate(result_messages) if isinstance(m, HumanMessage)),
                default=-1,
            )
            current_turn_messages = result_messages[last_human_idx + 1 :]

            for msg in current_turn_messages:
                if isinstance(msg, AIMessage):
                    # Stream text content tokens
                    if isinstance(msg.content, str) and msg.content.strip():
                        assistant_response_parts.append(msg.content)
                        yield {"type": "token", "content": msg.content}

                    # Gemini thinking models may return content as a list of
                    # parts (thought parts + text parts).  Extract text parts.
                    elif isinstance(msg.content, list):
                        for part in msg.content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text = part.get("text", "")
                                if text.strip():
                                    assistant_response_parts.append(text)
                                    yield {"type": "token", "content": text}

                    # Extract resolved city from tool call arguments
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if tool_call.get("name") in (
                                "get_current_weather",
                                "get_weather_forecast",
                                "compare_weather",
                                "get_clothing_advice",
                            ):
                                args = tool_call.get("args", {})
                                if "city" in args and resolved_city is None:
                                    resolved_city = args["city"]

            if resolved_city:
                yield {"type": "resolved_city", "city": resolved_city}

            # ── Persist the exchange (fail-soft; never breaks the response) ──
            if session_id:
                conversation_id = await ensure_conversation(
                    session_id=session_id,
                    user_id=user_id,
                    first_message=message,
                    city_name=city_context or resolved_city,
                )
                await save_exchange(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=message,
                    bot_response="".join(assistant_response_parts),
                    conversation_id=conversation_id,
                    city_resolved=resolved_city or city_context,
                )

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            # Never leak internals (stack traces, API keys, DB errors) to the client
            yield {
                "type": "error",
                "detail": "Something went wrong while generating a response. Please try again.",
            }


# ── HELPERS ───────────────────────────────────────────────────────────────────


def _enrich_message(
    message: str,
    city_context: Optional[str],
    unit: str,
    retrieved_context: Optional[str] = None,
) -> str:
    """
    Optionally prepend city/unit/retrieved-context to the user message.

    Keeps the agent's system prompt clean while giving it enough context
    to avoid an extra clarification round-trip.
    """
    parts: list[str] = []

    if city_context:
        parts.append(f"[Current city context: {city_context}]")

    if unit and unit.upper() in ("C", "F"):
        label = "Celsius" if unit.upper() == "C" else "Fahrenheit"
        parts.append(f"[Preferred temperature unit: {label}]")

    if retrieved_context:
        parts.append(retrieved_context)

    if parts:
        return " ".join(parts) + "\n\n" + message

    return message


# ── SINGLETON ─────────────────────────────────────────────────────────────────

_agent_instance: Optional[WeatherAgent] = None


def get_agent() -> WeatherAgent:
    """Get or create the agent singleton."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = WeatherAgent()
    return _agent_instance
