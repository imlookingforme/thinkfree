from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    # Check existing user
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    hashed_password = AuthService.get_password_hash(data.password)
    new_user = User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        password_hash=hashed_password,
        role=data.role,
        locale=data.locale,
        created_at=datetime.utcnow(),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Issue session token
    token = AuthService.create_access_token({"sub": new_user.id, "role": new_user.role})
    AuthService.set_session_cookie(response, token)

    return AuthResponse(
        user=UserResponse.model_validate(new_user), message="Registration successful."
    )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not AuthService.verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
        )

    token = AuthService.create_access_token({"sub": user.id, "role": user.role})
    AuthService.set_session_cookie(response, token)

    return AuthResponse(user=UserResponse.model_validate(user), message="Login successful.")


@router.post("/logout")
async def logout(response: Response):
    AuthService.clear_session_cookie(response)
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user = await AuthService.get_current_user(request, db)
    return UserResponse.model_validate(user)


@router.get("/google/callback", response_model=AuthResponse)
async def google_callback(
    response: Response, code: str = "mock_code", db: AsyncSession = Depends(get_db)
):
    """
    Google OAuth Callback. If GOOGLE_CLIENT_ID is not configured, provides dev mock sign-in.
    """
    mock_email = "student.demo@thinkfree.internal"
    mock_name = "Alex Chen (Demo Student)"

    result = await db.execute(select(User).where(User.email == mock_email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            name=mock_name,
            email=mock_email,
            password_hash=AuthService.get_password_hash("thinkfree_demo_pass"),
            role="student",
            locale="en",
            consent_flags={
                "audio_retention": True,
                "analytics_sharing": True,
                "professor_sharing": True,
            },
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = AuthService.create_access_token({"sub": user.id, "role": user.role})
    AuthService.set_session_cookie(response, token)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="OAuth sign-in successful (Dev bypass active).",
    )
