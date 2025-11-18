"""
Tests for user endpoints.
"""

import pytest
from httpx import AsyncClient

from src.models.user import User


@pytest.mark.asyncio
class TestUsers:
    """Test user endpoints."""
    
    async def test_get_user_profile(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test getting user profile."""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert "post_count" in data
        assert "total_views" in data
    
    async def test_update_profile(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating user profile."""
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
                "bio": "Updated bio",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
    
    async def test_update_password(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating password."""
        response = await client.put(
            "/api/v1/users/me/password",
            headers=auth_headers,
            json={
                "current_password": "TestPass123!",
                "new_password": "NewPass123!",
            },
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    async def test_update_password_wrong_current(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating password with wrong current password."""
        response = await client.put(
            "/api/v1/users/me/password",
            headers=auth_headers,
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewPass123!",
            },
        )
        
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]
    
    async def test_get_user_by_id(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test getting user by ID."""
        response = await client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
    
    async def test_list_users_admin_only(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test that listing users requires admin privileges."""
        response = await client.get(
            "/api/v1/users",
            headers=auth_headers,
        )
        
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]
    
    async def test_list_users_as_admin(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_user: User,
        test_admin: User
    ):
        """Test listing users as admin."""
        response = await client.get(
            "/api/v1/users",
            headers=admin_auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2  # At least test_user and test_admin
    
    async def test_admin_update_user(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_user: User
    ):
        """Test admin updating another user."""
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers,
            json={
                "is_verified": True,
                "is_active": True,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True
        assert data["is_active"] is True
    
    async def test_delete_account(
        self,
        client: AsyncClient,
        test_db,
    ):
        """Test deleting user account."""
        # Create a new user for deletion
        from src.repositories.user import UserRepository
        from src.schemas.user import UserCreate
        
        user_repo = UserRepository(test_db)
        user_data = UserCreate(
            email="delete@example.com",
            username="deleteuser",
            password="DeletePass123!",
        )
        user = await user_repo.create(user_data)
        
        # Create auth token
        from src.core.security import security_manager
        token = security_manager.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        # Delete account
        response = await client.delete(
            "/api/v1/users/me",
            headers=headers,
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify user is deleted
        deleted_user = await user_repo.get_by_id(user.id)
        assert deleted_user is None
