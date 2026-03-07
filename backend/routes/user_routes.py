from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import User
from auth import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/user", tags=["user"])


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    image: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class DeleteUserRequest(BaseModel):
    password: str


@router.get("")
def get_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    login_history = [
        {
            "id": h.id,
            "ip": h.ip,
            "user_agent": h.user_agent,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in sorted(current_user.login_history, key=lambda h: h.created_at, reverse=True)[:10]
    ]

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "image": current_user.image,
        "monthly_goal": current_user.monthly_goal,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "is_premium": current_user.subscription.status == "active" if current_user.subscription else False,
        "subscription": {
            "status": current_user.subscription.status if current_user.subscription else "inactive",
            "current_period_end": current_user.subscription.current_period_end.isoformat() if current_user.subscription and current_user.subscription.current_period_end else None,
        },
        "login_history": login_history,
    }


@router.put("")
def update_user(body: UpdateUserRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.name is not None:
        current_user.name = body.name

    if body.image is not None:
        current_user.image = body.image if body.image != "" else None

    if body.current_password and body.new_password:
        if not current_user.hashed_password:
            raise HTTPException(status_code=400, detail="Cannot change password for this account type")

        if not verify_password(body.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        if len(body.new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

        current_user.hashed_password = hash_password(body.new_password)

    db.commit()
    return {"success": True}


@router.delete("")
def delete_user(body: DeleteUserRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.hashed_password:
        if not verify_password(body.password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")

    db.delete(current_user)
    db.commit()
    return {"success": True}
