#!/usr/bin/env python
"""Test that critical packages are installed correctly"""

import sys

def test_imports():
    print("\n" + "="*50)
    print("Testing Package Imports")
    print("="*50)
    
    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "uvicorn",
        "pydantic": "BaseModel",
        "psycopg2": "psycopg2",
        "dotenv": "load_dotenv",
        "langchain_core": "tool",
        "langchain_ollama": "ChatOllama",
        "langgraph": "create_react_agent",
        "ollama": "Client",
        "slowapi": "Limiter",
        "structlog": "get_logger",
    }
    
    success = True
    for module, attr in packages.items():
        try:
            __import__(module)
            print(f"✓ {module:<25} - OK")
        except ImportError as e:
            print(f"✗ {module:<25} - FAILED: {e}")
            success = False
    
    return success

if __name__ == "__main__":
    sys.exit(0 if test_imports() else 1)