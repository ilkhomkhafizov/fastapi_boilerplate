"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication endpoints."""
    
    async def test_register(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "NewPass123!",
                "full_name": "New User",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data
    
    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "another_user",
                "password": "NewPass123!",
            },
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_login(self, client: AsyncClient, test_user: User):
        """Test user login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPass123!",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "WrongPass123!",
            },
        )
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    async def test_get_current_user(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test getting current user info."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    async def test_logout(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test user logout."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    async def test_refresh_token(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test refreshing access token."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPass123!",
            },
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    async def test_password_reset_request(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test password reset request."""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": test_user.email},
        )
        
        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]
