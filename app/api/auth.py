from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from arq import create_pool
from arq.connections import RedisSettings
from datetime import datetime, timedelta
import secrets
import httpx
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.rate_limiter import check_rate_limit
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.services.tracking_service import track_event
from pydantic import BaseModel, EmailStr

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for X-Forwarded-For header (if behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    # Rate limiting: Prevent registration spam
    client_ip = get_client_ip(request)
    is_limited, remaining = check_rate_limit(client_ip, "register")
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        plan="FREE"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Track registration
    track_event(db, "user.registered", user_id=user.id, event_data={"email": user.email})

    # Enqueue welcome email (J0)
    try:
        redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await redis_pool.enqueue_job('send_onboarding_welcome_email', user.id)
        await redis_pool.close()
    except Exception as e:
        # Don't fail registration if email fails
        pass

    return user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    # Rate limiting: Prevent brute force attacks
    is_limited, remaining = check_rate_limit(user_data.email, "login")
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in 5 minutes."
        )

    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(req_data: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Send password reset email."""
    # Rate limiting: Prevent abuse of password reset
    is_limited, remaining = check_rate_limit(req_data.email, "forgot_password")
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later."
        )

    user = db.query(User).filter(User.email == req_data.email).first()

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If your email is registered, you will receive a password reset link."}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.password_reset_token = reset_token
    user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    # Send reset email
    reset_url = f"{settings.APP_BASE_URL}/reset-password?token={reset_token}"

    try:
        redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await redis_pool.enqueue_job('send_password_reset_email', user.id, reset_url)
        await redis_pool.close()
    except Exception as e:
        # Don't fail if email service is down
        pass

    return {"message": "If your email is registered, you will receive a password reset link."}


@router.post("/reset-password")
def reset_password(req_data: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Reset password using token."""
    # Rate limiting: Prevent brute force on reset tokens
    client_ip = get_client_ip(request)
    is_limited, remaining = check_rate_limit(client_ip, "reset_password")
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many reset attempts. Please try again later."
        )

    user = db.query(User).filter(User.password_reset_token == req_data.token).first()

    if not user or not user.password_reset_expires_at or user.password_reset_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password
    user.hashed_password = get_password_hash(req_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.commit()

    return {"message": "Password reset successful"}


@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """Redirect to OAuth provider."""
    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Google OAuth not configured")

        redirect_uri = f"{settings.APP_BASE_URL}/api/auth/oauth/google/callback"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=openid email profile"
        )
        return RedirectResponse(url=auth_url, status_code=302)

    elif provider == "github":
        if not settings.GITHUB_CLIENT_ID:
            raise HTTPException(status_code=400, detail="GitHub OAuth not configured")

        redirect_uri = f"{settings.APP_BASE_URL}/api/auth/oauth/github/callback"
        auth_url = (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={settings.GITHUB_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=user:email"
        )
        return RedirectResponse(url=auth_url, status_code=302)

    else:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, db: Session = Depends(get_db)):
    """Handle OAuth callback."""
    try:
        if provider == "google":
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": f"{settings.APP_BASE_URL}/api/auth/oauth/google/callback",
                        "grant_type": "authorization_code",
                    }
                )
                token_data = token_response.json()
                access_token = token_data.get("access_token")

                # Get user info
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                user_data = user_response.json()

        elif provider == "github":
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "code": code,
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET,
                        "redirect_uri": f"{settings.APP_BASE_URL}/api/auth/oauth/github/callback",
                    },
                    headers={"Accept": "application/json"}
                )
                token_data = token_response.json()
                access_token = token_data.get("access_token")

                # Get user info
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                user_data = user_response.json()

        else:
            raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")

        # Find or create user
        email = user_data.get("email")
        oauth_id = str(user_data.get("id"))

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by OAuth provider")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user
            user = User(
                email=email,
                oauth_provider=provider,
                oauth_id=oauth_id,
                plan="FREE"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Track registration
            track_event(db, "user.registered", user_id=user.id, event_data={"email": email, "oauth_provider": provider})
        else:
            # Update OAuth info if not set
            if not user.oauth_provider:
                user.oauth_provider = provider
                user.oauth_id = oauth_id
                db.commit()

        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(user.id)})

        # Redirect to dashboard with token
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "redirect_url": f"{settings.APP_BASE_URL}/dashboard?token={jwt_token}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")
