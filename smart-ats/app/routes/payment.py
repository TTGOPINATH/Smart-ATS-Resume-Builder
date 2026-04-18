import os
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, Payment
from app.schemas.schemas import CreateOrderRequest, VerifyPaymentRequest
from app.utils.auth import get_current_user

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────
RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

PLANS = {
    "monthly": {
        "amount_paise": 49900,        # ₹499 in paise
        "amount_inr":   499,
        "currency":     "INR",
        "label":        "Pro Monthly",
        "description":  "Smart ATS Pro — Monthly Subscription",
        "duration_days": 30,
    },
    "yearly": {
        "amount_paise": 399900,       # ₹3999 in paise
        "amount_inr":   3999,
        "currency":     "INR",
        "label":        "Pro Yearly",
        "description":  "Smart ATS Pro — Annual Subscription (Save ₹2,000)",
        "duration_days": 365,
    },
}


# ── Razorpay client helper ────────────────────────────────────────────────────
def get_rzp():
    """Return a Razorpay client or raise a clear error."""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Payment gateway is not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to your .env file."
        )
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="razorpay package not installed. Run: pip install razorpay"
        )


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """HMAC-SHA256 signature verification."""
    payload  = f"{order_id}|{payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/plans")
def get_plans():
    """Return all available plans — no auth needed (used on pricing page)."""
    return {
        "plans": [
            {
                "id":       "monthly",
                "name":     "Pro Monthly",
                "price":    499,
                "currency": "INR",
                "period":   "month",
                "duration_days": 30,
                "features": [
                    "Unlimited ATS Scans",
                    "AI Resume Optimizer",
                    "Watermark-Free PDF Downloads",
                    "Job Description Matching",
                    "Full Resume History",
                    "Priority Email Support",
                ],
            },
            {
                "id":       "yearly",
                "name":     "Pro Yearly",
                "price":    3999,
                "currency": "INR",
                "period":   "year",
                "duration_days": 365,
                "savings":  "Save ₹2,000  •  2 months free",
                "features": [
                    "Everything in Monthly",
                    "2 Months Free",
                    "Download Tracking",
                    "Early Access to New Features",
                    "Dedicated Support",
                ],
            },
        ]
    }


# ── Authenticated endpoints ───────────────────────────────────────────────────

@router.post("/create-order")
def create_order(
    order_req: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Razorpay order and persist a pending Payment record."""
    plan = PLANS.get(order_req.plan)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Invalid plan '{order_req.plan}'. Choose 'monthly' or 'yearly'.")

    # Already premium?
    if current_user.is_premium and current_user.plan_expires_at and current_user.plan_expires_at > datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail=f"You are already on the {current_user.plan} plan, active until {current_user.plan_expires_at.strftime('%d %b %Y')}."
        )

    client = get_rzp()

    try:
        rzp_order = client.order.create({
            "amount":   plan["amount_paise"],
            "currency": plan["currency"],
            "receipt":  f"user_{current_user.id}_plan_{order_req.plan}",
            "notes": {
                "user_id":  str(current_user.id),
                "username": current_user.username,
                "plan":     order_req.plan,
            },
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay order creation failed: {str(e)}")

    # Persist pending payment
    payment = Payment(
        user_id=current_user.id,
        razorpay_order_id=rzp_order["id"],
        amount=plan["amount_inr"],
        currency=plan["currency"],
        plan=order_req.plan,
        status="pending",
    )
    db.add(payment)
    db.commit()

    return {
        "order_id":    rzp_order["id"],
        "amount":      plan["amount_paise"],   # paise — required by Razorpay JS
        "amount_inr":  plan["amount_inr"],
        "currency":    plan["currency"],
        "key_id":      RAZORPAY_KEY_ID,
        "plan_label":  plan["label"],
        "description": plan["description"],
        "user_name":   current_user.full_name or current_user.username,
        "user_email":  current_user.email,
    }


@router.post("/verify")
def verify_payment(
    verify_req: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify Razorpay payment signature, activate Pro, and return success payload.
    Called by the frontend after Razorpay checkout completes.
    """
    # 1. Signature check
    if not verify_razorpay_signature(
        verify_req.razorpay_order_id,
        verify_req.razorpay_payment_id,
        verify_req.razorpay_signature,
    ):
        # Mark as failed in DB
        payment = db.query(Payment).filter(
            Payment.razorpay_order_id == verify_req.razorpay_order_id
        ).first()
        if payment:
            payment.status = "failed"
            payment.failure_reason = "Signature mismatch"
            db.commit()
        raise HTTPException(status_code=400, detail="Payment signature verification failed. Contact support.")

    # 2. Fetch the pending payment record
    payment = db.query(Payment).filter(
        Payment.razorpay_order_id == verify_req.razorpay_order_id,
        Payment.user_id == current_user.id,
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    if payment.status == "success":
        # Idempotent — already processed
        return {
            "success": True,
            "message": "Payment already verified.",
            "plan": payment.plan,
            "already_processed": True,
        }

    # 3. Update payment record
    plan_config = PLANS.get(payment.plan, PLANS["monthly"])
    payment.razorpay_payment_id = verify_req.razorpay_payment_id
    payment.razorpay_signature  = verify_req.razorpay_signature
    payment.status              = "success"

    # 4. Activate / extend premium on user
    now = datetime.utcnow()
    # If already has active premium, extend from expiry; otherwise from now
    base = current_user.plan_expires_at if (
        current_user.is_premium
        and current_user.plan_expires_at
        and current_user.plan_expires_at > now
    ) else now

    current_user.is_premium       = True
    current_user.plan              = payment.plan
    current_user.plan_expires_at   = base + timedelta(days=plan_config["duration_days"])
    current_user.ats_scans_limit   = 999999

    db.commit()
    db.refresh(current_user)

    return {
        "success":     True,
        "message":     f"Welcome to Smart ATS Pro! Your {payment.plan} plan is now active.",
        "plan":        payment.plan,
        "expires_at":  current_user.plan_expires_at.strftime("%d %b %Y"),
        "payment_id":  verify_req.razorpay_payment_id,
    }


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Razorpay webhook endpoint.
    Configure in Razorpay Dashboard → Webhooks → https://yourdomain.com/payment/webhook
    Events: payment.captured, payment.failed, refund.created
    """
    body = await request.body()

    # Verify webhook signature
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    if webhook_secret:
        sig = request.headers.get("x-razorpay-signature", "")
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("event", "")
    payload    = event.get("payload", {})

    # ── payment.captured ──────────────────────────────────────────────────────
    if event_type == "payment.captured":
        entity     = payload.get("payment", {}).get("entity", {})
        order_id   = entity.get("order_id")
        payment_id = entity.get("id")

        if order_id:
            payment = db.query(Payment).filter(
                Payment.razorpay_order_id == order_id
            ).first()
            if payment and payment.status != "success":
                payment.razorpay_payment_id = payment_id
                payment.status = "success"

                user = db.query(User).filter(User.id == payment.user_id).first()
                if user:
                    plan_config = PLANS.get(payment.plan, PLANS["monthly"])
                    now  = datetime.utcnow()
                    base = user.plan_expires_at if (
                        user.is_premium and user.plan_expires_at and user.plan_expires_at > now
                    ) else now
                    user.is_premium      = True
                    user.plan            = payment.plan
                    user.plan_expires_at = base + timedelta(days=plan_config["duration_days"])
                    user.ats_scans_limit = 999999

                db.commit()

    # ── payment.failed ────────────────────────────────────────────────────────
    elif event_type == "payment.failed":
        entity   = payload.get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        reason   = entity.get("error_description", "Payment failed")
        if order_id:
            payment = db.query(Payment).filter(
                Payment.razorpay_order_id == order_id
            ).first()
            if payment and payment.status == "pending":
                payment.status         = "failed"
                payment.failure_reason = reason
                db.commit()

    # ── refund.created ────────────────────────────────────────────────────────
    elif event_type == "refund.created":
        entity     = payload.get("refund", {}).get("entity", {})
        payment_id = entity.get("payment_id")
        if payment_id:
            payment = db.query(Payment).filter(
                Payment.razorpay_payment_id == payment_id
            ).first()
            if payment:
                payment.status = "refunded"
                user = db.query(User).filter(User.id == payment.user_id).first()
                if user:
                    # Check if any other active payments exist
                    active = db.query(Payment).filter(
                        Payment.user_id == user.id,
                        Payment.status == "success"
                    ).first()
                    if not active:
                        user.is_premium      = False
                        user.plan            = "free"
                        user.plan_expires_at = None
                        user.ats_scans_limit = 3
                db.commit()

    return {"status": "ok"}


@router.get("/status")
def payment_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's subscription status."""
    now     = datetime.utcnow()
    active  = current_user.is_premium
    expires = current_user.plan_expires_at

    # Auto-expire if plan has passed
    if active and expires and expires < now:
        current_user.is_premium      = False
        current_user.plan            = "free"
        current_user.ats_scans_limit = 3
        db.commit()
        active = False

    return {
        "is_premium":      current_user.is_premium,
        "plan":            current_user.plan,
        "expires_at":      expires.strftime("%d %b %Y") if expires else None,
        "expires_at_raw":  expires.isoformat() if expires else None,
        "scans_used":      current_user.ats_scans_used,
        "scans_limit":     current_user.ats_scans_limit,
        "scans_remaining": "unlimited" if current_user.is_premium else max(0, current_user.ats_scans_limit - current_user.ats_scans_used),
    }


@router.get("/history")
def payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all payments for the current user."""
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return [
        {
            "id":                 p.id,
            "plan":               p.plan,
            "amount":             p.amount,
            "currency":           p.currency,
            "status":             p.status,
            "failure_reason":     p.failure_reason,
            "razorpay_order_id":  p.razorpay_order_id,
            "razorpay_payment_id":p.razorpay_payment_id,
            "created_at":         p.created_at.strftime("%d %b %Y, %H:%M"),
        }
        for p in payments
    ]
