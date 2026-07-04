from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.expenses import create_expenses, list_expenses
from app.schemas.expense import (
    ExpenseAnalyzeRequest,
    ExpenseAnalyzeResponse,
    ExpenseCreateRequest,
    ExpenseCreateResponse,
    ExpenseListItem,
    ExpenseListResponse,
)
from app.services.ai_parser import ExpenseAnalysisService

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.post("/analyze", response_model=ExpenseAnalyzeResponse)
def analyze_expense(payload: ExpenseAnalyzeRequest) -> ExpenseAnalyzeResponse:
    return ExpenseAnalysisService().analyze(payload.text)


@router.post("", response_model=ExpenseCreateResponse)
def save_expense(payload: ExpenseCreateRequest, db: Session = Depends(get_db)) -> ExpenseCreateResponse:
    expenses = create_expenses(db, payload)
    return ExpenseCreateResponse(ids=[expense.id for expense in expenses], saved=True)


@router.get("", response_model=ExpenseListResponse)
def get_expenses(
    month: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
) -> ExpenseListResponse:
    items = [
        ExpenseListItem(
            id=expense.id,
            date=expense.date,
            title=expense.title,
            category=expense.category,
            payment_amount=expense.payment_amount,
            my_share=expense.my_share,
            receivable_amount=expense.receivable_amount,
            payable_amount=expense.payable_amount,
            memo=expense.memo,
        )
        for expense in list_expenses(db, month=month, category=category)
    ]
    return ExpenseListResponse(items=items)
