from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User, FixedSubscription
from auth import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


class CreateSubscriptionRequest(BaseModel):
    platform: str
    price: float
    start_date: Optional[str] = None


class UpdateSubscriptionRequest(BaseModel):
    platform: Optional[str] = None
    price: Optional[float] = None
    start_date: Optional[str] = None


def serialize(sub: FixedSubscription):
    return {
        "id": sub.id,
        "platform": sub.platform,
        "price": sub.price,
        "start_date": sub.start_date.isoformat() if sub.start_date else None,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    }


@router.get("")
def get_subscriptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subs = (
        db.query(FixedSubscription)
        .filter(FixedSubscription.user_id == current_user.id)
        .order_by(FixedSubscription.created_at.desc())
        .all()
    )
    total_monthly = sum(s.price for s in subs)
    return {
        "subscriptions": [serialize(s) for s in subs],
        "total_monthly": total_monthly,
        "count": len(subs),
    }


@router.post("")
def create_subscription(
    body: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_premium = current_user.subscription and current_user.subscription.status == "active"
    if not is_premium:
        count = db.query(FixedSubscription).filter(FixedSubscription.user_id == current_user.id).count()
        if count >= 2:
            raise HTTPException(status_code=403, detail="Starter plan limit reached (2/2 subscriptions)")

    sub_date = datetime.fromisoformat(body.start_date) if body.start_date else datetime.utcnow()

    sub = FixedSubscription(
        user_id=current_user.id,
        platform=body.platform,
        price=body.price,
        start_date=sub_date,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    return serialize(sub)


@router.put("/{id}")
def update_subscription(
    id: str,
    body: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.query(FixedSubscription).filter(
        FixedSubscription.id == id,
        FixedSubscription.user_id == current_user.id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if body.platform is not None:
        sub.platform = body.platform
    if body.price is not None:
        sub.price = body.price
    if body.start_date is not None:
        sub.start_date = datetime.fromisoformat(body.start_date)

    db.commit()
    db.refresh(sub)
    return serialize(sub)


@router.delete("/{id}")
def delete_subscription(id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(FixedSubscription).filter(
        FixedSubscription.id == id,
        FixedSubscription.user_id == current_user.id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(sub)
    db.commit()
    return {"success": True}
