from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from arq import create_pool
from arq.connections import RedisSettings
from app.core.database import get_db
from app.core.supabase_client import get_supabase_admin, get_supabase_anon
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

    supabase = get_supabase_anon()
    auth_response = supabase.auth.sign_up({
        "email": user_data.email,
        "password": user_data.password
    })

    if auth_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )

    auth_user_id = auth_response.user.id
    user = db.query(User).filter(User.auth_user_id == auth_user_id).first()
    if user is None:
        user = User(
            email=user_data.email,
            auth_user_id=auth_user_id,
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
    except Exception:
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

    supabase = get_supabase_anon()
    auth_response = supabase.auth.sign_in_with_password({
        "email": user_data.email,
        "password": user_data.password
    })

    if auth_response.user is None or auth_response.session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    auth_user_id = auth_response.user.id
    user = db.query(User).filter(User.auth_user_id == auth_user_id).first()
    if user is None:
        user = User(
            email=user_data.email,
            auth_user_id=auth_user_id,
            plan="FREE"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"access_token": auth_response.session.access_token, "token_type": "bearer"}


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

    supabase = get_supabase_anon()
    supabase.auth.reset_password_for_email(
        req_data.email,
        {"redirect_to": f"{settings.APP_BASE_URL}/reset-password"}
    )

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

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password reset is handled via Supabase recovery link."
    )


@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """Redirect to OAuth provider."""
    if not settings.SUPABASE_URL:
        raise HTTPException(status_code=400, detail="Supabase not configured")

    if provider not in {"google", "github"}:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")

    redirect_uri = f"{settings.APP_BASE_URL}/auth-callback"
    auth_url = (
        f"{settings.SUPABASE_URL}/auth/v1/authorize?"
        f"provider={provider}&"
        f"redirect_to={redirect_uri}"
    )
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str):
    """Handle OAuth callback."""
    return RedirectResponse(url=f"{settings.APP_BASE_URL}/auth-callback", status_code=302)
