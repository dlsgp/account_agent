from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ExpenseParseRequest:
    text: str
    today: date | None = None


@dataclass(frozen=True)
class ExpenseParseEvent:
    date: date | None
    title: str | None
    total_amount: int | None
    payer: str | None
    people_count: int | None
    participants: list[str] = field(default_factory=list)
    settlement_type: str | None = None
    memo: str = ""
    missing_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExpenseParseResult:
    clarification_required: bool
    events: list[ExpenseParseEvent] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SettlementRequest:
    payment_amount: int
    people_count: int
    paid_by_me: bool
    settlement_type: str = "split"


@dataclass(frozen=True)
class SettlementResult:
    payment_amount: int
    my_share: int
    receivable_amount: int
    payable_amount: int


@dataclass(frozen=True)
class CategoryRequest:
    text: str


@dataclass(frozen=True)
class CategoryResult:
    category: str | None
    confidence: float
    needs_clarification: bool
    candidates: list[str] = field(default_factory=list)
