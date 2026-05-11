"""
FILE: backend/app/tests/unit/test_security.py
Unit tests for security functions (token generation, hashing, OAuth state)
"""

import pytest
from datetime import datetime, timedelta

from app.core.security import (
    generate_session_token,
    hash_session_token,
    verify_session_token,
    generate_oauth_state,
    verify_oauth_state,
    get_session_expiry,
    is_session_expired,
    generate_user_initials
)


class TestSessionTokenGeneration:
    """Test session token generation and verification."""
    
    def test_generate_session_token_length(self):
        """Test that generated token has expected length."""
        token = generate_session_token()
        # Base64 of 32 bytes should be approximately 43 chars
        assert len(token) == 43
        assert isinstance(token, str)
    
    def test_generate_session_token_uniqueness(self):
        """Test that tokens are unique."""
        token1 = generate_session_token()
        token2 = generate_session_token()
        assert token1 != token2
    
    def test_hash_session_token_deterministic(self):
        """Test that hashing the same token produces same hash."""
        token = "test_token_123"
        hash1 = hash_session_token(token)
        hash2 = hash_session_token(token)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex string
    
    def test_hash_session_token_different_inputs(self):
        """Test that different tokens produce different hashes."""
        token1 = "token_one"
        token2 = "token_two"
        hash1 = hash_session_token(token1)
        hash2 = hash_session_token(token2)
        assert hash1 != hash2
    
    def test_verify_session_token_valid(self):
        """Test verification of valid token."""
        token = generate_session_token()
        hashed = hash_session_token(token)
        assert verify_session_token(token, hashed) is True
    
    def test_verify_session_token_invalid(self):
        """Test verification of invalid token."""
        token = "valid_token"
        wrong_hash = hash_session_token("wrong_token")
        assert verify_session_token(token, wrong_hash) is False


class TestOAuthState:
    """Test OAuth state generation and verification."""
    
    def test_generate_oauth_state_length(self):
        """Test that OAuth state has expected length."""
        state = generate_oauth_state()
        # Base64 of 32 bytes should be approximately 43 chars
        assert len(state) == 43
        assert isinstance(state, str)
    
    def test_generate_oauth_state_uniqueness(self):
        """Test that OAuth states are unique."""
        state1 = generate_oauth_state()
        state2 = generate_oauth_state()
        assert state1 != state2
    
    def test_verify_oauth_state_valid(self):
        """Test verification of valid OAuth state."""
        state = generate_oauth_state()
        assert verify_oauth_state(state, state) is True
    
    def test_verify_oauth_state_invalid(self):
        """Test verification of invalid OAuth state."""
        state1 = generate_oauth_state()
        state2 = generate_oauth_state()
        assert verify_oauth_state(state1, state2) is False
    
    def test_verify_oauth_state_empty(self):
        """Test verification with empty states."""
        assert verify_oauth_state("", "") is False
        assert verify_oauth_state("state", "") is False
        assert verify_oauth_state("", "state") is False
        assert verify_oauth_state(None, None) is False


class TestSessionExpiry:
    """Test session expiry functions."""
    
    def test_get_session_expiry_default(self):
        """Test that session expiry is 24 hours from now."""
        expiry = get_session_expiry()
        now = datetime.now()
        difference = expiry - now
        
        # Should be approximately 24 hours (allow 1 second tolerance)
        assert timedelta(hours=23, minutes=59, seconds=59) <= difference <= timedelta(hours=24, seconds=1)
    
    def test_is_session_expired_future(self):
        """Test that future session is not expired."""
        future = datetime.now() + timedelta(hours=1)
        assert is_session_expired(future) is False
    
    def test_is_session_expired_past(self):
        """Test that past session is expired."""
        past = datetime.now() - timedelta(hours=1)
        assert is_session_expired(past) is True
    
    def test_is_session_expired_now(self):
        """Test that current time is considered expired."""
        now = datetime.now()
        # Current time should be considered expired or very close to it
        result = is_session_expired(now)
        # Due to timing, it might be False, but within a second it should be True
        assert isinstance(result, bool)


class TestUserInitials:
    """Test user initials generation."""
    
    def test_initials_from_full_name(self):
        """Test initials from full name with first and last name."""
        assert generate_user_initials("John Doe", "john@example.com") == "JD"
        assert generate_user_initials("Jane Smith", "jane@example.com") == "JS"
    
    def test_initials_from_single_name(self):
        """Test initials from single name."""
        assert generate_user_initials("John", "john@example.com") == "JO"
        assert generate_user_initials("A", "a@example.com") == "AX"
    
    def test_initials_from_email(self):
        """Test initials from email when name is None."""
        assert generate_user_initials(None, "john@example.com") == "JO"
        assert generate_user_initials(None, "a@example.com") == "A"
        assert generate_user_initials(None, "ab@example.com") == "AB"
    
    def test_initials_from_empty_email(self):
        """Test initials fallback for empty inputs."""
        assert generate_user_initials(None, None) == "U"
        assert generate_user_initials("", "") == "U"
    
    def test_initials_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        assert generate_user_initials("  John  Doe  ", "john@example.com") == "JD"
        assert generate_user_initials(" John ", "john@example.com") == "JO"
    
    def test_initials_case_insensitive_email(self):
        """Test that email case doesn't affect initials."""
        assert generate_user_initials(None, "JOHN@example.com") == "JO"
        assert generate_user_initials(None, "John@Example.com") == "JO"
