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


def test_create_monitor_then_list():
    db_name = f"test_monitors_{uuid.uuid4().hex}.db"
    _set_test_env(f"sqlite:///{db_name}")

    from app.core.database import Base, SessionLocal, engine
    from app.core.security import create_access_token
    from app.models.user import User
    from app.main import app

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    user = User(email="monitors@example.com", hashed_password="test", plan="FREE")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    token = create_access_token(data={"sub": str(user.id)})
    client = TestClient(app)

    response = client.post(
        "/api/monitors",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Immediate Monitor", "url": "https://example.com", "timeout": 60},
    )
    assert response.status_code == 200

    list_response = client.get(
        "/api/monitors",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200

    monitors = list_response.json()
    assert any(m["name"] == "Immediate Monitor" for m in monitors)
