"""
FILE: backend/app/agent/llm_provider.py
LLM provider factory for Ollama, Groq, Gemini
"""

from typing import Optional
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_llm():
    """
    Factory function to get the configured LLM based on LLM_PROVIDER env var.
    
    Returns:
        Configured LLM instance for use with LangGraph
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        return _get_ollama_llm()
    elif provider == "groq":
        return _get_groq_llm()
    elif provider == "gemini":
        return _get_gemini_llm()
    else:
        logger.warning(f"Unknown LLM provider: {provider}, defaulting to Ollama")
        return _get_ollama_llm()


def _get_ollama_llm():
    """Get Ollama LLM instance."""
    try:
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7,
            num_ctx=4096,
        )
        
        logger.info(f"Initialized Ollama LLM: {settings.OLLAMA_MODEL}")
        return llm
        
    except ImportError as e:
        logger.error(f"Failed to import langchain_ollama: {e}")
        raise ImportError("langchain_ollama is required for Ollama provider. Install with: pip install langchain-ollama")
    except Exception as e:
        logger.error(f"Failed to initialize Ollama LLM: {e}")
        raise


def _get_groq_llm():
    """Get Groq LLM instance."""
    try:
        from langchain_groq import ChatGroq
        
        if not hasattr(settings, 'GROQ_API_KEY') or not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured in environment variables")
        
        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        logger.info("Initialized Groq LLM: llama-3.3-70b-versatile")
        return llm
        
    except ImportError as e:
        logger.error(f"Failed to import langchain_groq: {e}")
        raise ImportError("langchain_groq is required for Groq provider. Install with: pip install langchain-groq")
    except Exception as e:
        logger.error(f"Failed to initialize Groq LLM: {e}")
        raise


def _get_gemini_llm():
    """Get Google Gemini LLM instance."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured in environment variables")
        
        llm = ChatGoogleGenerativeAI(
            api_key=settings.GEMINI_API_KEY,
            model="gemini-pro",
            temperature=0.7,
        )
        
        logger.info("Initialized Gemini LLM: gemini-pro")
        return llm
        
    except ImportError as e:
        logger.error(f"Failed to import langchain_google_genai: {e}")
        raise ImportError("langchain-google-genai is required for Gemini provider. Install with: pip install langchain-google-genai")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini LLM: {e}")
        raise