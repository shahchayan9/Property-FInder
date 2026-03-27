"""
Stripe embedded Checkout for Property Finder: pay a small amount to unlock
full listing details. Requires STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY in .env.

Important: this module reads env vars dynamically at runtime (not at import time),
because the agent loads dotenv after imports.
"""
from __future__ import annotations

import os
import time

try:
    import stripe
except ImportError:
    stripe = None

def _cfg() -> dict:
    secret_key = (os.getenv("STRIPE_SECRET_KEY", "") or "").strip()
    publishable_key = (os.getenv("STRIPE_PUBLISHABLE_KEY", "") or "").strip()
    try:
        amount_cents = int(os.getenv("STRIPE_AMOUNT_CENTS", "50"))
    except Exception:
        amount_cents = 50
    currency = (os.getenv("STRIPE_CURRENCY", "usd") or "usd").lower().strip() or "usd"
    product_name = (os.getenv("STRIPE_PRODUCT_NAME", "Listing details") or "Listing details").strip()
    success_url = (os.getenv("STRIPE_SUCCESS_URL", "https://agentverse.ai") or "https://agentverse.ai").rstrip("/")
    return {
        "secret_key": secret_key,
        "publishable_key": publishable_key,
        "amount_cents": amount_cents,
        "currency": currency,
        "product_name": product_name,
        "success_url": success_url,
    }


def get_amount_cents() -> int:
    return int(_cfg()["amount_cents"])


def is_configured() -> bool:
    c = _cfg()
    return bool(stripe and c["secret_key"] and c["publishable_key"])


def _get_stripe():
    if not stripe:
        return None
    stripe.api_key = _cfg()["secret_key"]
    return stripe


def _expires_at() -> int:
    sec = int(os.getenv("STRIPE_CHECKOUT_EXPIRES_SECONDS", "1800"))
    sec = max(1800, min(24 * 3600, sec))
    return int(time.time()) + sec


def create_hosted_checkout_session(
    *,
    user_address: str,
    chat_session_id: str,
    description: str,
    service: str = "listing_details",
) -> dict | None:
    """
    Create a Stripe hosted Checkout Session.
    Returns dict with checkout_url and checkout_session_id.
    User visits the URL in their browser to pay; we poll verify_checkout_session_paid()
    when they return to chat.
    """
    if not is_configured():
        return None
    s = _get_stripe()
    if not s:
        return None
    c = _cfg()
    try:
        success_url = (
            f"{c['success_url']}"
            f"?session_id={{CHECKOUT_SESSION_ID}}"
            f"&chat_session_id={chat_session_id}"
        )
        session = s.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            success_url=success_url,
            cancel_url=c["success_url"],
            expires_at=_expires_at(),
            line_items=[
                {
                    "price_data": {
                        "currency": c["currency"],
                        "product_data": {
                            "name": c["product_name"],
                            "description": description,
                        },
                        "unit_amount": int(c["amount_cents"]),
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "user_address": user_address,
                "session_id": chat_session_id,
                "service": service,
            },
        )
        return {
            "checkout_url": session.url,
            "id": session.id,
            "checkout_session_id": session.id,
            "currency": c["currency"],
            "amount_cents": int(c["amount_cents"]),
        }
    except Exception as exc:
        import traceback
        print(f"[stripe] ERROR creating hosted checkout: {exc}")
        traceback.print_exc()
        return None


def verify_checkout_session_paid(checkout_session_id: str) -> bool:
    if not is_configured():
        return False
    s = _get_stripe()
    if not s:
        return False
    try:
        session = s.checkout.Session.retrieve(checkout_session_id)
        return getattr(session, "payment_status", None) == "paid"
    except Exception:
        return False
