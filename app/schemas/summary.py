from __future__ import annotations

from pydantic import BaseModel


class CategorySummary(BaseModel):
    category: str
    payment_amount: int
    receivable_amount: int
    payable_amount: int
    my_share: int


class MonthlySummaryResponse(BaseModel):
    month: str
    categories: list[CategorySummary]
    total: CategorySummary
