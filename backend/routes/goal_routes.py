from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User
from auth import get_current_user

router = APIRouter(prefix="/api/goals", tags=["goals"])


class UpdateGoalRequest(BaseModel):
    monthly_goal: float


@router.get("")
def get_goal(current_user: User = Depends(get_current_user)):
    return {"monthly_goal": current_user.monthly_goal}


@router.put("")
def update_goal(body: UpdateGoalRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.monthly_goal = body.monthly_goal
    db.commit()
    return {"monthly_goal": current_user.monthly_goal}
