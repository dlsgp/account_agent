from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ExpenseRecord
from app.schemas.summary import CategorySummary, MonthlySummaryResponse

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.get("/monthly", response_model=MonthlySummaryResponse)
def get_monthly_summary(month: str, db: Session = Depends(get_db)) -> MonthlySummaryResponse:
    year, month_num = [int(part) for part in month.split("-", 1)]
    start = date(year, month_num, 1)
    end = date(year + int(month_num == 12), 1 if month_num == 12 else month_num + 1, 1)

    stmt = (
        select(
            ExpenseRecord.category,
            func.coalesce(func.sum(ExpenseRecord.payment_amount), 0),
            func.coalesce(func.sum(ExpenseRecord.receivable_amount), 0),
            func.coalesce(func.sum(ExpenseRecord.payable_amount), 0),
            func.coalesce(func.sum(ExpenseRecord.my_share), 0),
        )
        .where(ExpenseRecord.date >= start, ExpenseRecord.date < end)
        .group_by(ExpenseRecord.category)
        .order_by(ExpenseRecord.category)
    )

    categories = [
        CategorySummary(
            category=row[0],
            payment_amount=row[1],
            receivable_amount=row[2],
            payable_amount=row[3],
            my_share=row[4],
        )
        for row in db.execute(stmt)
    ]
    total = CategorySummary(
        category="전체",
        payment_amount=sum(item.payment_amount for item in categories),
        receivable_amount=sum(item.receivable_amount for item in categories),
        payable_amount=sum(item.payable_amount for item in categories),
        my_share=sum(item.my_share for item in categories),
    )
    return MonthlySummaryResponse(month=month, categories=categories, total=total)
