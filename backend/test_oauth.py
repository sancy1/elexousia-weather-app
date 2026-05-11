#!/usr/bin/env python
"""
FILE: backend/test_oauth.py
Test OAuth endpoints (manual - requires browser)
"""

print("\n" + "="*60)
print("Testing OAuth Social Login")
print("="*60)

print("\n🔗 Google OAuth URL:")
print("   http://localhost:8000/api/auth/google")
print("\n🔗 GitHub OAuth URL:")
print("   http://localhost:8000/api/auth/github")
print("\n📋 User Profile (after login):")
print("   http://localhost:8000/api/auth/me")
print("\n📋 To test:")
print("   1. Start server: python run.py")
print("   2. Open http://localhost:8000/api/auth/google")
print("   3. Approve Google login")
print("   4. You'll be redirected back")
print("   5. Check cookie in browser dev tools")
print("   6. Visit /api/auth/me to see your profile")
print("\n" + "="*60 + "\n")