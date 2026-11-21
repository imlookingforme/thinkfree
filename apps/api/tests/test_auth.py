import pytest
from httpx import AsyncClient
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register new user
    register_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "secure_password_123",
        "role": "student",
        "locale": "en",
    }
    res = await client.post("/api/v1/auth/register", json=register_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["role"] == "student"

    # 2. Check duplicate registration fails
    dup_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert dup_res.status_code == 409

    # 3. Login
    login_payload = {"email": "jane@example.com", "password": "secure_password_123"}
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "thinkfree_session" in login_res.cookies

    # 4. Get Current User via session cookie
    me_res = await client.get("/api/v1/auth/me", cookies=login_res.cookies)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Jane Doe"

    # 5. Logout
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    login_payload = {"email": "nonexistent@example.com", "password": "wrong_password"}
    res = await client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_me_returns_401(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(client: AsyncClient):
    # 1. Register user
    reg = await client.post(
        "/api/v1/auth/register",
        json={"name": "Alice Bob", "email": "alice@gmail.com", "password": "old_password_123"},
    )
    assert reg.status_code == 201
    user_id = reg.json()["user"]["id"]

    # 2. Request forgot password
    fp_res = await client.post("/api/v1/auth/forgot-password", json={"email": "alice@gmail.com"})
    assert fp_res.status_code == 200
    assert fp_res.json()["success"] is True

    # 3. Create a reset token (as generated during forgot-password)
    reset_token = AuthService.create_reset_token(user_id)

    # 4. Reset password
    rp_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "new_secure_password_456"},
    )
    assert rp_res.status_code == 200
    assert rp_res.json()["success"] is True

    # 5. Old password should now fail
    old_login = await client.post(
        "/api/v1/auth/login", json={"email": "alice@gmail.com", "password": "old_password_123"}
    )
    assert old_login.status_code == 401

    # 6. New password should succeed
    new_login = await client.post(
        "/api/v1/auth/login", json={"email": "alice@gmail.com", "password": "new_secure_password_456"}
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_google_login_flow(client: AsyncClient):
    # 1. Sign in with Google email
    google_res = await client.post(
        "/api/v1/auth/google",
        json={"email": "google_student@gmail.com", "name": "Google Student"},
    )
    assert google_res.status_code == 200
    data = google_res.json()
    assert data["user"]["email"] == "google_student@gmail.com"
    assert data["user"]["name"] == "Google Student"
    assert "thinkfree_session" in google_res.cookies

    # 2. Authenticated me endpoint
    me_res = await client.get("/api/v1/auth/me", cookies=google_res.cookies)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "google_student@gmail.com"
