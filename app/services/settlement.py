from __future__ import annotations

from app.skills import SettlementCalculatorSkill
from app.skills.models import SettlementRequest, SettlementResult


def calculate_settlement(
    payment_amount: int,
    people_count: int,
    paid_by_me: bool,
    settlement_type: str = "split",
) -> SettlementResult:
    return SettlementCalculatorSkill().run(
        SettlementRequest(
            payment_amount=payment_amount,
            people_count=people_count,
            paid_by_me=paid_by_me,
            settlement_type=settlement_type,
        )
    )
