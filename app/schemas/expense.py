from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ParticipantPreview(BaseModel):
    name: str
    receivable_amount: int = Field(ge=0)


class ExpenseAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)


class ExpensePreview(BaseModel):
    date: date
    title: str
    category: str
    total_amount: int = Field(ge=0)
    payer: str
    payment_amount: int = Field(ge=0)
    my_share: int = Field(ge=0)
    people_count: int | None = Field(default=None, ge=1)
    paid_by_me: bool
    receivable_amount: int = Field(ge=0)
    payable_amount: int = Field(ge=0)
    settlement_type: str = "split"
    type: str = "expense"
    memo: str | None = None
    raw_input: str
    participants: list[ParticipantPreview] = Field(default_factory=list)


class ExpenseAnalyzeResponse(BaseModel):
    status: str
    clarification_required: bool = False
    events: list[ExpensePreview] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    question: str | None = None


class ExpenseCreateRequest(BaseModel):
    events: list[ExpensePreview] = Field(min_length=1)


class ExpenseCreateResponse(BaseModel):
    ids: list[int]
    saved: bool


class ExpenseListItem(BaseModel):
    id: int
    date: date
    title: str
    category: str
    payment_amount: int
    my_share: int
    receivable_amount: int
    payable_amount: int
    memo: str | None


class ExpenseListResponse(BaseModel):
    items: list[ExpenseListItem]
