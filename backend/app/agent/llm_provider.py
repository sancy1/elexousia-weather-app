# """
# FILE: backend/app/agent/llm_provider.py
# LLM provider factory for Ollama, Groq, Gemini
# """

# from typing import Optional
# from app.core.config import settings
# from app.core.logging_config import get_logger

# logger = get_logger(__name__)


# def get_llm():
#     """
#     Factory function to get the configured LLM based on LLM_PROVIDER env var.
    
#     Returns:
#         Configured LLM instance for use with LangGraph
#     """
#     provider = settings.LLM_PROVIDER.lower()
    
#     if provider == "ollama":
#         return _get_ollama_llm()
#     elif provider == "groq":
#         return _get_groq_llm()
#     elif provider == "gemini":
#         return _get_gemini_llm()
#     else:
#         logger.warning(f"Unknown LLM provider: {provider}, defaulting to Ollama")
#         return _get_ollama_llm()


# def _get_ollama_llm():
#     """Get Ollama LLM instance."""
#     try:
#         from langchain_ollama import ChatOllama
        
#         llm = ChatOllama(
#             model=settings.OLLAMA_MODEL,
#             base_url=settings.OLLAMA_BASE_URL,
#             temperature=0.7,
#             num_ctx=4096,
#         )
        
#         logger.info(f"Initialized Ollama LLM: {settings.OLLAMA_MODEL}")
#         return llm
        
#     except ImportError as e:
#         logger.error(f"Failed to import langchain_ollama: {e}")
#         raise ImportError("langchain_ollama is required for Ollama provider. Install with: pip install langchain-ollama")
#     except Exception as e:
#         logger.error(f"Failed to initialize Ollama LLM: {e}")
#         raise


# def _get_groq_llm():
#     """Get Groq LLM instance."""
#     try:
#         from langchain_groq import ChatGroq
        
#         if not hasattr(settings, 'GROQ_API_KEY') or not settings.GROQ_API_KEY:
#             raise ValueError("GROQ_API_KEY not configured in environment variables")
        
#         llm = ChatGroq(
#             api_key=settings.GROQ_API_KEY,
#             model="llama-3.3-70b-versatile",
#             temperature=0.7,
#         )
        
#         logger.info("Initialized Groq LLM: llama-3.3-70b-versatile")
#         return llm
        
#     except ImportError as e:
#         logger.error(f"Failed to import langchain_groq: {e}")
#         raise ImportError("langchain_groq is required for Groq provider. Install with: pip install langchain-groq")
#     except Exception as e:
#         logger.error(f"Failed to initialize Groq LLM: {e}")
#         raise


# def _get_gemini_llm():
#     """Get Google Gemini LLM instance."""
#     try:
#         from langchain_google_genai import ChatGoogleGenerativeAI
        
#         if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
#             raise ValueError("GEMINI_API_KEY not configured in environment variables")
        
#         llm = ChatGoogleGenerativeAI(
#             api_key=settings.GEMINI_API_KEY,
#             model="gemini-pro",
#             temperature=0.7,
#         )
        
#         logger.info("Initialized Gemini LLM: gemini-pro")
#         return llm
        
#     except ImportError as e:
#         logger.error(f"Failed to import langchain_google_genai: {e}")
#         raise ImportError("langchain-google-genai is required for Gemini provider. Install with: pip install langchain-google-genai")
#     except Exception as e:
#         logger.error(f"Failed to initialize Gemini LLM: {e}")
#         raise
















# =====================================================================================================











# """
# FILE: backend/app/agent/llm_provider.py
# LLM provider factory for Ollama, Groq, Gemini
# """

# from typing import Optional
# from app.core.config import settings
# from app.core.logging_config import get_logger

# logger = get_logger(__name__)


# def get_llm():
#     """
#     Factory function to get the configured LLM based on LLM_PROVIDER env var.
    
#     Returns:
#         Configured LLM instance for use with LangGraph
#     """
#     provider = settings.LLM_PROVIDER.lower()
    
#     if provider == "ollama":
#         return _get_ollama_llm()
#     elif provider == "groq":
#         return _get_groq_llm()
#     elif provider == "gemini":
#         return _get_gemini_llm()
#     else:
#         logger.warning(f"Unknown LLM provider: {provider}, defaulting to Ollama")
#         return _get_ollama_llm()


# def _get_ollama_llm():
#     """Get Ollama LLM instance."""
#     try:
#         from langchain_ollama import ChatOllama
        
#         llm = ChatOllama(
#             model=settings.OLLAMA_MODEL,
#             base_url=settings.OLLAMA_BASE_URL,
#             temperature=0.7,
#             num_ctx=4096,
#         )
        
#         logger.info(f"Initialized Ollama LLM: {settings.OLLAMA_MODEL}")
#         return llm
        
#     except ImportError as e:
#         logger.error(f"Failed to import langchain_ollama: {e}")
#         raise ImportError("langchain_ollama is required for Ollama provider. Install with: pip install langchain-ollama")
#     except Exception as e:
#         logger.error(f"Failed to initialize Ollama LLM: {e}")
#         raise


# def _get_groq_llm():
#     """Get Groq LLM instance."""
#     try:
#         from langchain_groq import ChatGroq
        
#         if not settings.GROQ_API_KEY:
#             raise ValueError("GROQ_API_KEY not configured in environment variables")
        
#         llm = ChatGroq(
#             api_key=settings.GROQ_API_KEY,
#             model=settings.GROQ_MODEL,
#             temperature=0.7,
#         )
        
#         logger.info(f"Initialized Groq LLM: {settings.GROQ_MODEL}")
#         return llm
        
#     except ImportError as e:
#         logger.error(f"Failed to import langchain_groq: {e}")
#         raise ImportError("langchain_groq is required for Groq provider. Install with: pip install langchain-groq")
#     except Exception as e:
#         logger.error(f"Failed to initialize Groq LLM: {e}")
#         raise


# def _get_gemini_llm():
#     """Get Google Gemini LLM instance."""
#     try:
#         from langchain_google_genai import ChatGoogleGenerativeAI
        
#         if not settings.GOOGLE_API_KEY:
#             raise ValueError("GOOGLE_API_KEY not configured in environment variables")
        
#         llm = ChatGoogleGenerativeAI(
#             api_key=settings.GOOGLE_API_KEY,
#             model=settings.GEMINI_MODEL,
#             temperature=0.7,
#         )
        
#         logger.info(f"Initialized Gemini LLM: {settings.GEMINI_MODEL}")
#         return llm
        
#     except ImportError as e:
#         logger.error(f"Failed to import langchain_google_genai: {e}")
#         raise ImportError("langchain-google-genai is required for Gemini provider. Install with: pip install langchain-google-genai")
#     except Exception as e:
#         logger.error(f"Failed to initialize Gemini LLM: {e}")
#         raise










































"""
FILE: backend/app/agent/llm_provider.py
LLM provider factory for Ollama, Groq, Gemini
Fixed: Gemini thought_signature support for tool/function calling
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


# ── OLLAMA ────────────────────────────────────────────────────────────────────

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
        raise ImportError(
            "langchain_ollama is required for Ollama provider. "
            "Install with: pip install langchain-ollama"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Ollama LLM: {e}")
        raise


# ── GROQ ──────────────────────────────────────────────────────────────────────

def _get_groq_llm():
    """Get Groq LLM instance."""
    try:
        from langchain_groq import ChatGroq

        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not configured in environment variables"
            )

        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.7,
        )

        logger.info(f"Initialized Groq LLM: {settings.GROQ_MODEL}")
        return llm

    except ImportError as e:
        logger.error(f"Failed to import langchain_groq: {e}")
        raise ImportError(
            "langchain_groq is required for Groq provider. "
            "Install with: pip install langchain-groq"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Groq LLM: {e}")
        raise


# ── GEMINI ────────────────────────────────────────────────────────────────────

# Models that use extended thinking and require thought_signature passthrough.
# Gemini 2.5 thinking models mandate this when function/tool calling is active.
_GEMINI_THINKING_MODELS = {
    "gemini-2.5-pro",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-pro-preview-03-25",
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.0-flash-thinking-exp",
}


def _is_thinking_model(model_name: str) -> bool:
    """Return True if the configured model requires thought_signature handling."""
    name = model_name.lower()
    return any(tm in name for tm in _GEMINI_THINKING_MODELS)


def _get_gemini_llm():
    """
    Get Google Gemini LLM instance.

    For thinking models (Gemini 2.5 family), we must:
      1. Pass include_thoughts=True so the API returns thought_signature fields.
      2. Forward those signatures back in subsequent tool-result turns.

    LangChain's ChatGoogleGenerativeAI handles step 2 automatically when the
    model_kwargs below are set, as long as langchain-google-genai >= 2.1.0.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not configured in environment variables"
            )

        model_name: str = settings.GEMINI_MODEL
        thinking = _is_thinking_model(model_name)

        # Base kwargs shared by all Gemini models
        init_kwargs: dict = {
            "google_api_key": settings.GOOGLE_API_KEY,
            "model": model_name,
            "temperature": 0.7,
            # Keep tool-call responses valid JSON so the agent parser never
            # chokes on unexpected markdown or prose wrappers.
            "convert_system_message_to_human": False,
        }

        if thinking:
            # ------------------------------------------------------------------
            # Thought-signature fix for Gemini 2.5 thinking models
            #
            # The Gemini API attaches a `thought_signature` to every function-
            # call part when thinking is enabled. On the very next request we
            # MUST echo that signature back inside the corresponding
            # function-result part, otherwise Gemini raises:
            #   "Function call is missing a thought_signature …"
            #
            # Setting include_thoughts=True in generation_config makes the API
            # return the signatures. LangChain >= 2.1.0 then automatically
            # copies them into the next request's tool-result parts.
            # ------------------------------------------------------------------
            init_kwargs["model_kwargs"] = {
                "generation_config": {
                    "include_thoughts": True,
                }
            }
            logger.info(
                f"Gemini thinking model detected ({model_name}): "
                "thought_signature passthrough enabled."
            )
        else:
            logger.info(
                f"Gemini standard model ({model_name}): "
                "thought_signature passthrough not required."
            )

        llm = ChatGoogleGenerativeAI(**init_kwargs)

        logger.info(f"Initialized Gemini LLM: {model_name}")
        return llm

    except ImportError as e:
        logger.error(f"Failed to import langchain_google_genai: {e}")
        raise ImportError(
            "langchain-google-genai is required for Gemini provider. "
            "Install with: pip install langchain-google-genai"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini LLM: {e}")
        raise


# ── OPTIONAL: bind_tools wrapper ─────────────────────────────────────────────
# LangGraph typically calls llm.bind_tools(tools) before passing the LLM into
# the graph.  For thinking models we need to make sure that bind_tools also
# carries the include_thoughts generation config.  The helper below is a
# convenience wrapper you can use in weather_agent.py if the plain bind_tools
# call still omits the flag after upgrading langchain-google-genai.

def get_llm_with_tools(tools: list):
    """
    Return an LLM already bound to *tools*, with the correct Gemini
    thought_signature config when a thinking model is active.

    Usage in weather_agent.py:
        from app.agent.llm_provider import get_llm_with_tools
        llm_with_tools = get_llm_with_tools([get_current_weather, ...])

    For Ollama / Groq this is equivalent to:
        get_llm().bind_tools(tools)
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini" and _is_thinking_model(settings.GEMINI_MODEL):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                google_api_key=settings.GOOGLE_API_KEY,
                model=settings.GEMINI_MODEL,
                temperature=0.7,
                convert_system_message_to_human=False,
            )

            # bind_tools with tool_config ensures Gemini knows these are
            # real callable tools, not just schema examples, which triggers
            # the thought_signature mechanism correctly.
            return llm.bind_tools(
                tools,
                tool_config={"function_calling_config": {"mode": "AUTO"}},
            )
        except Exception as e:
            logger.error(f"Failed to bind tools to Gemini thinking LLM: {e}")
            raise

    # For all other providers, standard bind_tools is sufficient
    return get_llm().bind_tools(tools)