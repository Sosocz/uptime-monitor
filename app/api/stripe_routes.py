from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import stripe
from app.core.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-checkout")
@router.post("/create-checkout/", include_in_schema=False)
async def create_checkout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if not settings.STRIPE_PRICE_ID_MONTHLY or settings.STRIPE_PRICE_ID_MONTHLY == "price_xxxxx":
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(email=current_user.email)
            current_user.stripe_customer_id = customer.id
            db.commit()
        
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": settings.STRIPE_PRICE_ID_MONTHLY, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.APP_BASE_URL}/dashboard?success=true",
            cancel_url=f"{settings.APP_BASE_URL}/dashboard?canceled=true",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-portal")
@router.post("/create-portal/", include_in_schema=False)
async def create_portal(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No subscription found")
        
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.APP_BASE_URL}/dashboard",
        )
        return {"portal_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
@router.post("/webhook/", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.stripe_subscription_id = subscription_id
            user.plan = "PAID"
            db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.stripe_subscription_id = None
            user.plan = "FREE"
            db.commit()
    
    return {"status": "success"}
