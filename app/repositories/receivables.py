from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExpenseRecord, Receivable


def list_receivables(db: Session, status: str = "pending", person_name: str | None = None) -> list[tuple[Receivable, ExpenseRecord]]:
    stmt = (
        select(Receivable, ExpenseRecord)
        .join(ExpenseRecord, ExpenseRecord.id == Receivable.expense_id)
        .where(Receivable.status == status)
        .order_by(ExpenseRecord.date.desc(), Receivable.id.desc())
    )
    if person_name:
        stmt = stmt.where(Receivable.person_name == person_name)
    return list(db.execute(stmt).all())
