from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel

from database import get_db
from models import User, Transaction
from auth import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

CATEGORIES_KEYWORDS = {
    "Food & Dining": ["grocery", "restaurant", "food", "uber eats", "doordash", "grubhub", "mcdonald", "starbucks", "coffee", "lunch", "dinner", "breakfast"],
    "Transportation": ["gas", "fuel", "uber", "lyft", "taxi", "parking", "transit", "bus", "subway", "train"],
    "Shopping": ["amazon", "walmart", "target", "ebay", "clothes", "shoes", "mall", "store", "purchase"],
    "Entertainment": ["netflix", "spotify", "hulu", "movie", "theater", "concert", "game", "subscription"],
    "Bills & Utilities": ["electric", "water", "internet", "phone", "rent", "mortgage", "insurance", "bill", "utility"],
    "Health": ["pharmacy", "doctor", "hospital", "gym", "fitness", "medical", "dentist", "health"],
    "Income": ["salary", "paycheck", "deposit", "freelance", "payment", "wage", "income", "bonus"],
}


def categorize(description: str) -> str:
    desc_lower = description.lower()
    for cat, keywords in CATEGORIES_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                return cat
    return "Other"


class CreateTransactionRequest(BaseModel):
    amount: float
    description: str
    category: Optional[str] = None
    type: str = "expense"
    date: Optional[str] = None
    recurring: bool = False


@router.get("")
def get_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.date.desc())
        .all()
    )

    now = datetime.utcnow()
    monthly_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.user_id == current_user.id,
            extract("year", Transaction.date) == now.year,
            extract("month", Transaction.date) == now.month,
        )
        .scalar()
    )

    return {
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "description": t.description,
                "category": t.category,
                "type": t.type,
                "date": t.date.isoformat() if t.date else None,
                "recurring": t.recurring,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in transactions
        ],
        "monthly_count": monthly_count or 0,
    }


@router.post("")
def create_transaction(
    body: CreateTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_premium = current_user.subscription and current_user.subscription.status == "active"

    if not is_premium:
        now = datetime.utcnow()
        monthly_count = (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.user_id == current_user.id,
                extract("year", Transaction.date) == now.year,
                extract("month", Transaction.date) == now.month,
            )
            .scalar()
        )
        if (monthly_count or 0) >= 12:
            raise HTTPException(status_code=403, detail="Monthly limit reached (12/12)")

    final_category = body.category or categorize(body.description)
    tx_date = datetime.fromisoformat(body.date) if body.date else datetime.utcnow()

    transaction = Transaction(
        user_id=current_user.id,
        amount=body.amount,
        description=body.description,
        category=final_category,
        type=body.type,
        date=tx_date,
        recurring=body.recurring,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        "id": transaction.id,
        "amount": transaction.amount,
        "description": transaction.description,
        "category": transaction.category,
        "type": transaction.type,
        "date": transaction.date.isoformat() if transaction.date else None,
        "recurring": transaction.recurring,
    }


@router.delete("")
def delete_transaction(id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == id, Transaction.user_id == current_user.id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"success": True}
