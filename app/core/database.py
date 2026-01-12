from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def _get_database_url() -> str:
    if settings.SUPABASE_DB_URL:
        return settings.SUPABASE_DB_URL
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    raise ValueError("DATABASE_URL or SUPABASE_DB_URL must be configured.")


engine = create_engine(_get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
