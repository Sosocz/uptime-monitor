"""
Status Page Subscribers API Routes
Endpoints for managing status page email subscribers.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
import secrets

from app.core.database import get_db
from app.models.status_page import StatusPage
from app.models.status_page_subscriber import StatusPageSubscriber

router = APIRouter()


# === Schemas ===

class SubscribeRequest(BaseModel):
    """Request to subscribe to a status page."""
    email: EmailStr
    notify_incidents: bool = True
    notify_maintenance: bool = True


class SubscriberResponse(BaseModel):
    """Status page subscriber response."""
    id: int
    email: str
    is_verified: bool
    notify_incidents: bool
    notify_maintenance: bool
    subscribed_at: datetime

    class Config:
        from_attributes = True


# === Public Endpoints (no auth required) ===

@router.post("/{slug}/subscribe")
def subscribe_to_status_page(
    slug: str,
    request: SubscribeRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Subscribe to a status page using email.

    Better Stack feature: Status page email subscriptions.
    Public endpoint - no authentication required.

    Args:
        slug: Status page slug
        request: Subscription request with email and preferences
    """
    # Find status page
    status_page = db.query(StatusPage).filter(
        StatusPage.slug == slug
    ).first()

    if not status_page:
        raise HTTPException(status_code=404, detail="Status page not found")

    # Check subscriber quota
    if status_page.subscriber_count >= status_page.subscriber_quota:
        raise HTTPException(
            status_code=400,
            detail=f"Subscriber limit reached ({status_page.subscriber_quota})"
        )

    # Check if already subscribed
    existing = db.query(StatusPageSubscriber).filter(
        StatusPageSubscriber.status_page_id == status_page.id,
        StatusPageSubscriber.email == request.email
    ).first()

    if existing:
        return {
            "success": True,
            "message": "Already subscribed",
            "subscriber_id": existing.id,
            "requires_verification": not existing.is_verified
        }

    # Create subscriber
    subscriber = StatusPageSubscriber(
        status_page_id=status_page.id,
        email=request.email,
        notify_incidents=request.notify_incidents,
        notify_maintenance=request.notify_maintenance,
        is_verified=False,
        verification_token=secrets.token_urlsafe(32),
        unsubscribe_token=secrets.token_urlsafe(32)
    )

    db.add(subscriber)

    # Update subscriber count
    status_page.subscriber_count = status_page.subscriber_count + 1

    db.commit()
    db.refresh(subscriber)

    # TODO: Send verification email
    # send_verification_email(subscriber.email, subscriber.verification_token)

    return {
        "success": True,
        "message": "Subscription created. Please check your email to verify.",
        "subscriber_id": subscriber.id,
        "requires_verification": True
    }


@router.post("/{slug}/verify/{token}")
def verify_subscriber(
    slug: str,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify a subscriber's email address.

    Public endpoint - no authentication required.
    """
    status_page = db.query(StatusPage).filter(
        StatusPage.slug == slug
    ).first()

    if not status_page:
        raise HTTPException(status_code=404, detail="Status page not found")

    subscriber = db.query(StatusPageSubscriber).filter(
        StatusPageSubscriber.status_page_id == status_page.id,
        StatusPageSubscriber.verification_token == token
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid verification token")

    if subscriber.is_verified:
        return {"success": True, "message": "Email already verified"}

    subscriber.is_verified = True
    db.commit()

    return {
        "success": True,
        "message": "Email verified successfully"
    }


@router.post("/{slug}/unsubscribe/{token}")
def unsubscribe_from_status_page(
    slug: str,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from a status page.

    Public endpoint - no authentication required.
    """
    status_page = db.query(StatusPage).filter(
        StatusPage.slug == slug
    ).first()

    if not status_page:
        raise HTTPException(status_code=404, detail="Status page not found")

    subscriber = db.query(StatusPageSubscriber).filter(
        StatusPageSubscriber.status_page_id == status_page.id,
        StatusPageSubscriber.unsubscribe_token == token
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe token")

    # Delete subscriber
    db.delete(subscriber)

    # Update subscriber count
    status_page.subscriber_count = max(0, status_page.subscriber_count - 1)

    db.commit()

    return {
        "success": True,
        "message": "Successfully unsubscribed"
    }


# === Admin Endpoints (auth required) ===

@router.get("/{slug}/subscribers", response_model=List[SubscriberResponse])
def list_subscribers(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    List all subscribers for a status page.

    Admin endpoint - requires authentication in production.
    For now, it's public for demo purposes.
    """
    status_page = db.query(StatusPage).filter(
        StatusPage.slug == slug
    ).first()

    if not status_page:
        raise HTTPException(status_code=404, detail="Status page not found")

    subscribers = db.query(StatusPageSubscriber).filter(
        StatusPageSubscriber.status_page_id == status_page.id
    ).all()

    return subscribers


@router.get("/{slug}/subscribers/stats")
def get_subscriber_stats(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get subscriber statistics for a status page.

    Better Stack feature: Subscriber analytics.
    """
    status_page = db.query(StatusPage).filter(
        StatusPage.slug == slug
    ).first()

    if not status_page:
        raise HTTPException(status_code=404, detail="Status page not found")

    subscribers = db.query(StatusPageSubscriber).filter(
        StatusPageSubscriber.status_page_id == status_page.id
    ).all()

    verified = sum(1 for s in subscribers if s.is_verified)
    unverified = len(subscribers) - verified

    return {
        "total_subscribers": len(subscribers),
        "verified_subscribers": verified,
        "unverified_subscribers": unverified,
        "subscriber_quota": status_page.subscriber_quota,
        "quota_usage_percent": round((len(subscribers) / status_page.subscriber_quota) * 100, 2) if status_page.subscriber_quota > 0 else 0
    }
