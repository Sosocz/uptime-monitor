import os
import uuid
from datetime import datetime, timedelta

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


def test_monitor_metrics_and_page():
    db_name = f"test_monitor_metrics_{uuid.uuid4().hex}.db"
    _set_test_env(f"sqlite:///{db_name}")

    from app.core.database import Base, SessionLocal, engine
    from app.core.security import create_access_token
    from app.models.user import User
    from app.models.monitor import Monitor
    from app.models.check import Check
    from app.main import app

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    user = User(email="metrics@example.com", hashed_password="test", plan="FREE")
    db.add(user)
    db.commit()
    db.refresh(user)

    monitor = Monitor(user_id=user.id, name="Metrics Monitor", url="https://example.com", interval=60, timeout=30)
    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    now = datetime.utcnow()
    checks = [
        Check(monitor_id=monitor.id, status="up", response_time=120, checked_at=now - timedelta(hours=2)),
        Check(monitor_id=monitor.id, status="up", response_time=180, checked_at=now - timedelta(hours=1)),
        Check(monitor_id=monitor.id, status="up", response_time=150, checked_at=now - timedelta(minutes=30)),
    ]
    db.add_all(checks)
    db.commit()
    db.close()

    token = create_access_token(data={"sub": str(user.id)})
    client = TestClient(app)

    page_response = client.get(f"/monitors/{monitor.id}")
    assert page_response.status_code == 200

    metrics_response = client.get(
        f"/api/monitors/{monitor.id}/metrics?range=day",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert metrics_response.status_code == 200
    data = metrics_response.json()
    assert data.get("points")
    assert len(data["points"]) > 0
