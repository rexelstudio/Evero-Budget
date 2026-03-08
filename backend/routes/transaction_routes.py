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
    "Food & Dining 🍽️": ["restaurant", "food", "uber eats", "doordash", "grubhub", "mcdonald", "starbucks", "coffee", "lunch", "dinner", "breakfast", "cafe", "pizza"],
    "Groceries 🛒": ["grocery", "supermarket", "walmart", "target", "tesco", "kroger", "whole foods", "aldi", "asda", "costco"],
    "Transportation 🚗": ["uber", "lyft", "taxi", "parking", "transit", "bus", "subway", "train"],
    "Gas ⛽️": ["gas", "fuel", "shell", "chevron", "bp", "exxon", "mobil", "costco gas"],
    "Shopping 🛍️": ["amazon", "ebay", "clothes", "shoes", "mall", "store", "purchase", "nike", "adidas", "zara", "h&m"],
    "Entertainment 🎬": ["movie", "theater", "concert", "game", "book", "museum", "cinema", "ticket"],
    "Bills & Utilities 📄": ["electric", "water", "internet", "phone", "rent", "mortgage", "insurance", "bill", "utility", "gas bill", "council tax"],
    "Health 💊": ["pharmacy", "doctor", "hospital", "dentist", "medical", "drugstore", "cvs", "walgreens"],
    "Housing 🏠": ["rent", "mortgage", "housing", "apartment", "maintenance", "repairs"],
    "Personal Care ✨": ["barber", "salon", "haircut", "spa", "makeup", "skincare", "cosmetics"],
    "Education 🎓": ["tuition", "school", "college", "university", "bookstore", "course"],
    "Travel ✈️": ["flight", "hotel", "airbnb", "vacation", "booking", "airline"],
    "Pets 🐾": ["vet", "pet food", "grooming", "chewy", "petsmart", "dog", "cat"],
    "Gifts & Donations 🎁": ["charity", "donation", "gift", "present", "birthday"],
    "Investments 📈": ["stock", "crypto", "bitcoin", "dividend", "brokerage"],
    "Insurance 🛡️": ["insurance", "geico", "progressive", "allstate", "state farm", "premium", "health insurance", "car insurance"],
    "Salary 💼": ["salary", "paycheck", "payroll", "wage", "direct deposit"],
    "Freelance 💻": ["freelance", "upwork", "fiverr", "contract", "consulting", "payment"],
    "Investment Income 🏦": ["dividend", "interest", "capital gain", "brokerage", "fidelity", "vanguard"],
    "Rental Income 🏘️": ["rent income", "airbnb", "tenant", "property"],
    "Bonuses 🎊": ["bonus", "commission", "incentive", "award"],
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


@router.delete("/{id}")
def delete_transaction(id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == id, Transaction.user_id == current_user.id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"success": True}
