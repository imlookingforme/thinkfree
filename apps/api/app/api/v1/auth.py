import secrets
from datetime import datetime
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    GenericResponse,
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email.lower().strip()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
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

    # Send welcome email in background
    try:
        await EmailService.send_welcome_email(new_user.email, new_user.name)
    except Exception as e:
        print(f"Non-critical welcome email notice: {e}")

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


@router.post("/forgot-password", response_model=GenericResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    email_clean = data.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email_clean))
    user = result.scalar_one_or_none()

    if user:
        reset_token = AuthService.create_reset_token(user.id, expires_minutes=30)
        sent = await EmailService.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.name,
        )
        if not sent:
            print(f"Warning: SMTP dispatch failed for {user.email}")

    # Standard security practice: return uniform message to prevent email enumeration
    return GenericResponse(
        success=True,
        message="If an account is associated with this email, a password reset link has been dispatched to your inbox.",
    )


@router.post("/reset-password", response_model=GenericResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    user_id = AuthService.verify_reset_token(data.token)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account associated with this reset token no longer exists.",
        )

    user.password_hash = AuthService.get_password_hash(data.new_password)
    await db.commit()

    return GenericResponse(
        success=True,
        message="Your password has been reset successfully. You may now sign in with your new password.",
    )


@router.post("/google", response_model=AuthResponse)
async def google_login(data: GoogleLoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    # Handle Google Identity Services JWT credential if present
    if data.credential:
        try:
            claims = jwt.decode(data.credential, options={"verify_signature": False})
            user_email = claims.get("email")
            user_name = claims.get("name")
        except Exception as e:
            print(f"Google JWT parse warning: {e}")

    # Fallback to direct fields
    if not user_email and data.email:
        user_email = str(data.email)
    if not user_name and data.name:
        user_name = data.name

    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid Google account email or credential is required.",
        )

    email_clean = user_email.lower().strip()
    name_clean = user_name.strip() if user_name else email_clean.split("@")[0].title()

    # Find existing or create new user
    result = await db.execute(select(User).where(User.email == email_clean))
    user = result.scalar_one_or_none()

    if not user:
        random_pass = secrets.token_urlsafe(32)
        user = User(
            name=name_clean,
            email=email_clean,
            password_hash=AuthService.get_password_hash(random_pass),
            role="student",
            locale="en",
            created_at=datetime.utcnow(),
            consent_flags={
                "audio_retention": True,
                "analytics_sharing": True,
                "professor_sharing": True,
            },
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        try:
            await EmailService.send_welcome_email(user.email, user.name)
        except Exception as e:
            print(f"Non-critical welcome email notice: {e}")

    token = AuthService.create_access_token({"sub": user.id, "role": user.role})
    AuthService.set_session_cookie(response, token)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="Google sign-in successful.",
    )
