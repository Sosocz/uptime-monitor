from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.supabase_auth import fetch_supabase_user
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        supabase_user = await fetch_supabase_user(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase auth not configured"
        )
    if not supabase_user or not supabase_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    user = db.query(User).filter(User.auth_user_id == supabase_user["id"]).first()
    if user is None:
        user = User(
            email=supabase_user.get("email", ""),
            auth_user_id=supabase_user["id"],
            plan="FREE"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
