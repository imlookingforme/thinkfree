import pytest
from httpx import AsyncClient


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
