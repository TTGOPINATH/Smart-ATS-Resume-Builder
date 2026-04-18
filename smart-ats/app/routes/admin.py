from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import User, Resume, Payment
from app.utils.auth import require_admin

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), admin=Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar()
    premium_users = db.query(func.count(User.id)).filter(User.is_premium == True).scalar()
    total_resumes = db.query(func.count(Resume.id)).scalar()
    total_payments = db.query(func.count(Payment.id)).filter(Payment.status == "success").scalar()
    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "success").scalar() or 0

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "free_users": total_users - premium_users,
        "total_resumes": total_resumes,
        "successful_payments": total_payments,
        "total_revenue_inr": round(total_revenue, 2)
    }


@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "is_premium": u.is_premium,
            "is_active": u.is_active,
            "ats_scans_used": u.ats_scans_used,
            "created_at": u.created_at
        }
        for u in users
    ]


@router.put("/users/{user_id}/toggle-premium")
def toggle_premium(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_premium = not user.is_premium
    if user.is_premium:
        user.ats_scans_limit = 99999
    else:
        user.ats_scans_limit = 3
    db.commit()
    return {"user_id": user_id, "is_premium": user.is_premium}


@router.put("/users/{user_id}/toggle-active")
def toggle_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"user_id": user_id, "is_active": user.is_active}


@router.get("/payments")
def list_payments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "plan": p.plan,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "razorpay_order_id": p.razorpay_order_id,
            "created_at": p.created_at
        }
        for p in payments
    ]
