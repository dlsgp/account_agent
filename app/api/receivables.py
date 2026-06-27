from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.receivables import list_receivables
from app.schemas.receivable import ReceivableGroup, ReceivableListResponse, ReceivablePersonResponse, ReceivableRecord

router = APIRouter(prefix="/api/receivables", tags=["receivables"])


@router.get("", response_model=ReceivableListResponse)
def get_receivables(status: str = "pending", db: Session = Depends(get_db)) -> ReceivableListResponse:
    groups = _group_receivables(list_receivables(db, status=status))
    return ReceivableListResponse(items=list(groups.values()))


@router.get("/{person_name}", response_model=ReceivablePersonResponse)
def get_receivable_by_person(
    person_name: str,
    status: str = "pending",
    db: Session = Depends(get_db),
) -> ReceivablePersonResponse:
    groups = _group_receivables(list_receivables(db, status=status, person_name=person_name))
    return groups.get(person_name, ReceivablePersonResponse(person_name=person_name, total_amount=0, records=[]))


def _group_receivables(rows) -> dict[str, ReceivablePersonResponse]:
    grouped: dict[str, ReceivablePersonResponse] = {}
    for receivable, expense in rows:
        group = grouped.setdefault(
            receivable.person_name,
            ReceivablePersonResponse(person_name=receivable.person_name, total_amount=0, records=[]),
        )
        group.total_amount += receivable.amount
        group.records.append(
            ReceivableRecord(
                expense_id=expense.id,
                date=expense.date,
                title=expense.title,
                amount=receivable.amount,
            )
        )
    return grouped
