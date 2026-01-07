import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(user_email: str, user_id: int) -> str:
    """Create a Stripe Checkout session for subscription."""
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": settings.STRIPE_PRICE_ID_MONTHLY,
            "quantity": 1,
        }],
        mode="subscription",
        success_url=f"{settings.APP_BASE_URL}/dashboard?success=true",
        cancel_url=f"{settings.APP_BASE_URL}/dashboard?canceled=true",
        customer_email=user_email,
        metadata={"user_id": user_id}
    )
    return session.url


def create_customer_portal_session(customer_id: str) -> str:
    """Create a Stripe Customer Portal session for managing subscriptions."""
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.APP_BASE_URL}/dashboard"
    )
    return session.url
