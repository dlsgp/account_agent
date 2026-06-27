from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ReceivableRecord(BaseModel):
    expense_id: int
    date: date
    title: str
    amount: int


class ReceivableGroup(BaseModel):
    person_name: str
    total_amount: int
    records: list[ReceivableRecord]


class ReceivableListResponse(BaseModel):
    items: list[ReceivableGroup]


class ReceivablePersonResponse(ReceivableGroup):
    pass
