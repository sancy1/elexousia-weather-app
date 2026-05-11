"""
FILE: backend/app/agent/weather_agent.py
Core weather agent runner using LangGraph
"""

from typing import Dict, Any, Optional, AsyncIterator
import json
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.llm_provider import get_llm
from app.agent.tools.weather_tools import get_current_weather, get_weather_forecast, compare_weather
from app.agent.tools.city_resolver import resolve_city
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class WeatherAgent:
    """Weather agent powered by LangGraph"""
    
    def __init__(self):
        self.llm = get_llm()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph for the weather agent"""
        tools = [get_current_weather, get_weather_forecast, compare_weather]
        
        # Bind tools to the LLM (required for Groq)
        llm_with_tools = self.llm.bind_tools(tools)
        
        return create_react_agent(model=llm_with_tools, tools=tools, prompt=SYSTEM_PROMPT)
    
    async def run_query(
        self,
        message: str,
        session_id: Optional[str] = None,
        city_context: Optional[str] = None,
        unit: str = "C"
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run a weather query with streaming support
        
        Args:
            message: User's message
            session_id: Session identifier for conversation history
            city_context: Current city context
            unit: Temperature unit (C or F)
            
        Yields:
            Dict with SSE event data
        """
        yield {"type": "start", "session_id": session_id}
        
        try:
            # Run the graph with async invocation
            result = await self.graph.ainvoke({"messages": [HumanMessage(content=message)]})
            
            # Stream the final response and extract resolved city
            resolved_city = None
            for msg in result["messages"]:
                if isinstance(msg, AIMessage):
                    if isinstance(msg.content, str):
                        yield {"type": "token", "content": msg.content}
                    # Check tool calls for resolved city
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if tool_call.get('name') in ['get_current_weather', 'get_weather_forecast', 'compare_weather']:
                                # Try to extract city from tool arguments
                                args = tool_call.get('args', {})
                                if 'city' in args:
                                    resolved_city = args['city']
            
            # Send resolved city if found
            if resolved_city:
                yield {"type": "resolved_city", "city": resolved_city}
            
            yield {"type": "done"}
            
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            yield {"type": "error", "detail": str(e)}


# Singleton instance
_agent_instance: Optional[WeatherAgent] = None


def get_agent() -> WeatherAgent:
    """Get or create the agent singleton"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = WeatherAgent()
    return _agent_instance
