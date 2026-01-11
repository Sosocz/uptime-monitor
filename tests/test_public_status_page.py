import os
import uuid

from fastapi.testclient import TestClient


def _set_test_env(db_url: str) -> None:
    os.environ["DATABASE_URL"] = db_url
    os.environ["JWT_SECRET"] = "test_jwt_secret"
    os.environ["SMTP_HOST"] = "smtp.test.local"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "test"
    os.environ["SMTP_PASS"] = "test"
    os.environ["SMTP_FROM"] = "test@example.com"
    os.environ["TELEGRAM_BOT_TOKEN"] = "test"
    os.environ["STRIPE_SECRET_KEY"] = "sk_test"
    os.environ["STRIPE_PUBLISHABLE_KEY"] = "pk_test"
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    os.environ["STRIPE_PRICE_ID_MONTHLY"] = "price_test"
    os.environ["APP_BASE_URL"] = "http://testserver"


def test_public_status_page_route():
    db_name = f"test_status_pages_{uuid.uuid4().hex}.db"
    _set_test_env(f"sqlite:///{db_name}")

    from app.core.database import Base, SessionLocal, engine
    from app.models.user import User
    from app.models.status_page import StatusPage
    from app.main import app

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    user = User(email="status@example.com", hashed_password="test", plan="FREE")
    db.add(user)
    db.commit()
    db.refresh(user)

    page = StatusPage(user_id=user.id, name="Status", slug="soso", is_public=True)
    db.add(page)
    db.commit()
    db.close()

    client = TestClient(app)
    response = client.get("/status/soso")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
