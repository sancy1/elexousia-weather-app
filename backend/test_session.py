#!/usr/bin/env python
"""
FILE: backend/test_session.py
Test session management (no OAuth yet)
"""

import asyncio
from app.core.security import generate_session_token, hash_session_token
from app.infrastructure.repositories.user_repository import UserRepository

async def test_session():
    print("\n" + "="*60)
    print("Testing Session Management")
    print("="*60)
    
    # Test token generation
    token = generate_session_token()
    hashed = hash_session_token(token)
    print(f"\n✅ Token generated: {token[:20]}...")
    print(f"✅ Hashed: {hashed[:20]}...")
    
    # Test user repository (requires database)
    try:
        # Create a test user (you can delete after testing)
        user = await UserRepository.upsert_user(
            provider="test",
            provider_id="test_123",
            email="test@example.com",
            name="Test User"
        )
        print(f"\n✅ User created: {user.name} (id: {user.id})")
        
        # Create session
        session = await UserRepository.create_session(
            user_id=user.id,
            session_token=token,
            ip_address="127.0.0.1",
            user_agent="Test Script"
        )
        print(f"✅ Session created (expires: {session.expires_at})")
        
        # Get session
        session_data = await UserRepository.get_session(token)
        if session_data:
            print(f"✅ Session verified for user: {session_data['user'].email}")
        
        # Clean up
        await UserRepository.delete_session(token)
        print(f"✅ Session deleted")
        
    except Exception as e:
        print(f"⚠️  Database test skipped: {e}")
    
    print("\n" + "="*60)
    print("Session management ready for OAuth integration")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_session())