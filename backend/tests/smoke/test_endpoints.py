"""Smoke tests for post-deployment validation.

These tests verify critical endpoints are operational after deployment.
Run against staging/production URLs to validate deployments.

Usage:
    pytest tests/smoke/ --base-url=https://staging.example.com
"""

import pytest
from httpx import AsyncClient, Response
import json


# Base URL can be overridden via pytest flag
@pytest.fixture
def base_url(request):
    """Base URL for smoke tests (override with --base-url flag)."""
    return request.config.getoption("--base-url", default="http://localhost:8000")


@pytest.fixture
async def client(base_url):
    """HTTP client for smoke tests."""
    async with AsyncClient(base_url=base_url, timeout=10.0) as client:
        yield client


class TestHealthEndpoints:
    """Smoke tests for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_liveness_probe(self, client: AsyncClient):
        """Verify liveness probe responds (basic server health)."""
        response = await client.get("/health/live")
        
        assert response.status_code == 200, f"Liveness probe failed: {response.text}"
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_readiness_probe(self, client: AsyncClient):
        """Verify readiness probe responds (checks dependencies)."""
        response = await client.get("/health/ready")
        
        assert response.status_code == 200, f"Readiness probe failed: {response.text}"
        data = response.json()
        assert data["status"] == "ready"
        
        # Verify Redis connectivity
        assert "redis" in data.get("checks", {}), "Redis check missing"
        assert data["checks"]["redis"] == "connected", "Redis not connected"


class TestChatEndpoint:
    """Smoke tests for chat message endpoint."""
    
    @pytest.mark.asyncio
    async def test_chat_message_basic(self, client: AsyncClient):
        """Verify chat endpoint accepts messages and returns responses."""
        payload = {
            "message": "I want to fly from San Francisco to New York next week",
            "session_id": None  # New session
        }
        
        response = await client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Chat endpoint failed: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "response" in data, "Missing 'response' field"
        assert "session_id" in data, "Missing 'session_id' field"
        assert isinstance(data["response"], str), "Response is not a string"
        assert len(data["response"]) > 0, "Empty response"
    
    @pytest.mark.asyncio
    async def test_chat_message_validation(self, client: AsyncClient):
        """Verify input validation rejects invalid payloads."""
        # Test empty message
        response = await client.post(
            "/api/v1/chat/message",
            json={"message": ""},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422, "Empty message should be rejected"
    
    @pytest.mark.asyncio
    async def test_chat_message_max_length(self, client: AsyncClient):
        """Verify message length limit is enforced (2000 chars)."""
        long_message = "a" * 2001  # Exceeds MAX_MESSAGE_LENGTH
        
        response = await client.post(
            "/api/v1/chat/message",
            json={"message": long_message},
            headers={"Content-Type": "application/json"}
        )
        
        # Should either truncate (200) or reject (422)
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"


class TestSessionManagement:
    """Smoke tests for session persistence."""
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, client: AsyncClient):
        """Verify sessions persist across multiple requests."""
        # First request - create new session
        response1 = await client.post(
            "/api/v1/chat/message",
            json={"message": "Hello", "session_id": None}
        )
        assert response1.status_code == 200
        
        session_id = response1.json()["session_id"]
        assert session_id, "No session_id returned"
        
        # Second request - use same session
        response2 = await client.post(
            "/api/v1/chat/message",
            json={"message": "Follow-up message", "session_id": session_id}
        )
        assert response2.status_code == 200
        
        # Verify same session_id returned
        assert response2.json()["session_id"] == session_id, "Session ID changed"


class TestRateLimiting:
    """Smoke tests for rate limiting (if enabled)."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_not_triggered(self, client: AsyncClient):
        """Verify normal usage doesn't trigger rate limits."""
        # Send 3 requests (well below rate limit)
        for i in range(3):
            response = await client.post(
                "/api/v1/chat/message",
                json={"message": f"Test message {i}"}
            )
            assert response.status_code == 200, f"Request {i} was rate limited"


class TestErrorHandling:
    """Smoke tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_404_not_found(self, client: AsyncClient):
        """Verify 404 responses for invalid endpoints."""
        response = await client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_405_method_not_allowed(self, client: AsyncClient):
        """Verify 405 responses for invalid HTTP methods."""
        response = await client.put("/api/v1/chat/message")
        assert response.status_code == 405


# Pytest configuration for custom flags
def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost:8000",
        help="Base URL for smoke tests (e.g., https://staging.example.com)"
    )


# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Mark all tests as smoke tests."""
    for item in items:
        item.add_marker(pytest.mark.smoke)
