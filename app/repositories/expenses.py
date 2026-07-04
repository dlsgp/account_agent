from __future__ import annotations

from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import ExpenseRecord, Receivable
from app.schemas.expense import ExpenseCreateRequest


def create_expense_event(db: Session, data) -> ExpenseRecord:
    expense = ExpenseRecord(
        date=data.date,
        title=data.title,
        category=data.category,
        payment_amount=data.payment_amount,
        my_share=data.my_share,
        people_count=data.people_count,
        paid_by_me=data.paid_by_me,
        receivable_amount=data.receivable_amount,
        payable_amount=data.payable_amount,
        type=data.type,
        memo=data.memo,
        raw_input=data.raw_input,
    )
    for participant in data.participants:
        if participant.name == "me" or participant.receivable_amount <= 0:
            continue
        expense.receivables.append(
            Receivable(
                person_name=participant.name,
                amount=participant.receivable_amount,
                status="pending",
            )
        )
    db.add(expense)
    return expense


def create_expenses(db: Session, data: ExpenseCreateRequest) -> list[ExpenseRecord]:
    expenses = [create_expense_event(db, event) for event in data.events]
    db.commit()
    for expense in expenses:
        db.refresh(expense)
    return expenses


def list_expenses(db: Session, month: str | None = None, category: str | None = None) -> list[ExpenseRecord]:
    stmt: Select[tuple[ExpenseRecord]] = select(ExpenseRecord).order_by(ExpenseRecord.date.desc(), ExpenseRecord.id.desc())
    if month:
        year, month_num = [int(part) for part in month.split("-", 1)]
        start = date(year, month_num, 1)
        end = date(year + int(month_num == 12), 1 if month_num == 12 else month_num + 1, 1)
        stmt = stmt.where(ExpenseRecord.date >= start, ExpenseRecord.date < end)
    if category:
        stmt = stmt.where(ExpenseRecord.category == category)
    return list(db.scalars(stmt))
