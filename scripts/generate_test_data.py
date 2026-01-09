#!/usr/bin/env python3
"""
Script pour générer des données de test pour screenshots Product Hunt.

Usage:
    python scripts/generate_test_data.py --email test@example.com --password testpass123

Crée:
- 4 monitors avec vrais sites
- Checks avec response times réalistes
- 1 status page publique
- 1 incident résolu (pour historique)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.status_page import StatusPage, StatusPageMonitor
from app.models.incident import Incident
from app.core.security import get_password_hash
import random


def create_test_data(email: str, password: str):
    """Crée un compte de test avec données réalistes pour screenshots."""
    db = SessionLocal()

    try:
        # 1. Créer user de test
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                plan="PRO"  # PRO pour voir toutes les features
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ User créé: {email}")
        else:
            print(f"ℹ️  User existe déjà: {email}")

        # 2. Créer 4 monitors réalistes
        monitors_data = [
            {"name": "TrezApp Landing", "url": "https://trezapp.com", "uptime": 99.98},
            {"name": "API Backend", "url": "https://api.trezapp.com", "uptime": 99.95},
            {"name": "Status Page", "url": "https://status.trezapp.com", "uptime": 100.0},
            {"name": "Blog", "url": "https://blog.trezapp.com", "uptime": 99.90}
        ]

        monitors = []
        for i, data in enumerate(monitors_data):
            monitor = db.query(Monitor).filter(
                Monitor.user_id == user.id,
                Monitor.name == data["name"]
            ).first()

            if not monitor:
                monitor = Monitor(
                    user_id=user.id,
                    name=data["name"],
                    url=data["url"],
                    interval=60,  # 1 min (PRO)
                    timeout=10,
                    is_active=True,
                    last_status="up",
                    last_checked_at=datetime.utcnow()
                )
                db.add(monitor)
                db.commit()
                db.refresh(monitor)
                print(f"✅ Monitor créé: {data['name']}")

            monitors.append(monitor)

            # 3. Créer checks historiques (90 derniers jours)
            check_count = db.query(Check).filter(Check.monitor_id == monitor.id).count()
            if check_count < 100:
                # Créer 200 checks sur 90 jours
                for day in range(90):
                    checks_per_day = random.randint(20, 30)
                    for _ in range(checks_per_day):
                        check_time = datetime.utcnow() - timedelta(days=day, minutes=random.randint(0, 1439))

                        # 99.9% uptime = 99.9% de checks "up"
                        is_up = random.random() < (data["uptime"] / 100)

                        check = Check(
                            monitor_id=monitor.id,
                            status="up" if is_up else "down",
                            status_code=200 if is_up else random.choice([500, 502, 503, 0]),
                            response_time=random.randint(50, 300) if is_up else None,
                            error_message=None if is_up else "Connection timeout",
                            checked_at=check_time
                        )
                        db.add(check)

                db.commit()
                print(f"✅ Checks créés pour {data['name']}")

        # 4. Créer 1 incident résolu (pour montrer l'historique)
        incident = db.query(Incident).filter(Incident.monitor_id == monitors[1].id).first()
        if not incident:
            incident = Incident(
                monitor_id=monitors[1].id,
                user_id=user.id,
                incident_type="recovery",
                started_at=datetime.utcnow() - timedelta(days=2, hours=3),
                resolved_at=datetime.utcnow() - timedelta(days=2, hours=1),
                duration_seconds=7200,  # 2 hours
                cause="Server timeout (502)",
                failed_checks_count=12,
                status_code=502,
                error_message="Bad Gateway"
            )
            db.add(incident)
            db.commit()
            print(f"✅ Incident créé (résolu)")

        # 5. Créer status page publique
        status_page = db.query(StatusPage).filter(StatusPage.user_id == user.id).first()
        if not status_page:
            status_page = StatusPage(
                user_id=user.id,
                name="TrezApp Services",
                slug="trezapp-demo",
                is_public=True,
                header_text="All systems operational. Monitored 24/7.",
                brand_color="#3b82f6",
                show_powered_by=False  # PRO user
            )
            db.add(status_page)
            db.commit()
            db.refresh(status_page)

            # Ajouter les 3 premiers monitors
            for i, monitor in enumerate(monitors[:3]):
                page_monitor = StatusPageMonitor(
                    status_page_id=status_page.id,
                    monitor_id=monitor.id,
                    position=i
                )
                db.add(page_monitor)

            db.commit()
            print(f"✅ Status page créée: /status/trezapp-demo")

        print("\n" + "="*60)
        print("✅ DONNÉES DE TEST CRÉÉES")
        print("="*60)
        print(f"\nLogin: {email}")
        print(f"Password: {password}")
        print(f"\nDashboard: http://localhost:8000/dashboard")
        print(f"Status Page: http://localhost:8000/status/trezapp-demo")
        print("\nScreenshots à prendre:")
        print("1. Dashboard → Tous les monitors")
        print("2. Monitor detail → Response time graph")
        print("3. Status page → Vue publique")
        print("4. Incident history → Incident résolu")
        print("\n💡 Tip: Ouvre en mode incognito pour screenshots clean")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Génère des données de test pour screenshots PH")
    parser.add_argument("--email", default="demo@trezapp.com", help="Email du user de test")
    parser.add_argument("--password", default="demo123", help="Password du user de test")

    args = parser.parse_args()

    print("🚀 Génération des données de test...\n")
    create_test_data(args.email, args.password)
