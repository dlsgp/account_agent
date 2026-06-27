from __future__ import annotations

from app.skills.base import Skill
from app.skills.models import SettlementRequest, SettlementResult


class SettlementCalculatorSkill(Skill[SettlementRequest, SettlementResult]):
    """Calculate actual burden and settlement amounts from payment facts."""

    name = "settlement_calculator"

    def run(self, data: SettlementRequest) -> SettlementResult:
        if data.payment_amount <= 0:
            raise ValueError("payment_amount must be greater than 0")
        if data.people_count <= 0:
            raise ValueError("people_count must be greater than 0")

        my_share = data.payment_amount // data.people_count

        if data.paid_by_me:
            receivable_amount = data.payment_amount - my_share
            payable_amount = 0
        else:
            receivable_amount = 0
            payable_amount = my_share

        return SettlementResult(
            payment_amount=data.payment_amount,
            my_share=my_share,
            receivable_amount=receivable_amount,
            payable_amount=payable_amount,
        )
