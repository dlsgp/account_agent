from __future__ import annotations

from datetime import date

from app.core.config import settings
from app.schemas.expense import ExpenseAnalyzeResponse, ExpensePreview, ParticipantPreview
from app.services.settlement import calculate_settlement
from app.skills import CategoryClassifierSkill, ExpenseParserSkill
from app.skills.models import CategoryRequest, ExpenseParseEvent, ExpenseParseRequest


class ExpenseAnalysisService:
    def __init__(self) -> None:
        self.expense_parser = ExpenseParserSkill()
        self.category_classifier = CategoryClassifierSkill()

    def analyze(self, text: str, today: date | None = None) -> ExpenseAnalyzeResponse:
        # The deterministic skill parser is the source of truth for MVP multi-event behavior.
        return self._analyze_with_skills(text, today=today)

    def _analyze_with_skills(self, text: str, today: date | None = None) -> ExpenseAnalyzeResponse:
        parsed = self.expense_parser.run(ExpenseParseRequest(text=text, today=today))
        events: list[ExpensePreview] = []
        missing_fields = set(parsed.missing_fields)

        for event in parsed.events:
            category = self.category_classifier.run(CategoryRequest(text=event.memo))
            event_missing = list(event.missing_fields)
            if category.needs_clarification:
                event_missing.append("category")
            if event_missing:
                missing_fields.update(event_missing)
                continue

            assert event.date is not None
            assert event.total_amount is not None
            assert event.people_count is not None
            assert event.payer is not None
            assert event.settlement_type is not None
            assert category.category is not None

            paid_by_me = event.payer == "me"
            settlement = calculate_settlement(
                event.total_amount,
                event.people_count,
                paid_by_me,
                event.settlement_type,
            )
            preview = ExpensePreview(
                date=event.date,
                title=event.title or self._build_title(event.memo, category.category),
                category=category.category,
                total_amount=event.total_amount,
                payer=event.payer,
                payment_amount=settlement.payment_amount,
                my_share=settlement.my_share,
                people_count=event.people_count,
                paid_by_me=paid_by_me,
                receivable_amount=settlement.receivable_amount,
                payable_amount=settlement.payable_amount,
                settlement_type=event.settlement_type,
                memo=self._build_memo(event),
                raw_input=text,
                participants=self._build_participants(event, settlement.receivable_amount),
            )
            events.append(preview)

        clarification_required = bool(missing_fields)
        return ExpenseAnalyzeResponse(
            status="needs_clarification" if clarification_required else "ready",
            clarification_required=clarification_required,
            events=[] if clarification_required else events,
            missing_fields=sorted(missing_fields),
            question=self._build_question(sorted(missing_fields)) if clarification_required else None,
        )

    def _build_participants(self, event: ExpenseParseEvent, receivable_amount: int) -> list[ParticipantPreview]:
        settlement_targets = [name for name in event.participants if name != "me"]
        if receivable_amount <= 0 or not settlement_targets:
            return [ParticipantPreview(name=name, receivable_amount=0) for name in event.participants]

        base_amount = receivable_amount // len(settlement_targets)
        participant_rows = [ParticipantPreview(name="me", receivable_amount=0)]
        for index, name in enumerate(settlement_targets):
            amount = base_amount
            if index == len(settlement_targets) - 1:
                amount = receivable_amount - (base_amount * (len(settlement_targets) - 1))
            participant_rows.append(ParticipantPreview(name=name, receivable_amount=amount))
        return participant_rows

    def _build_question(self, missing_fields: list[str]) -> str:
        labels = {
            "date": "날짜",
            "total_amount": "총 금액",
            "people_count": "함께한 인원 수",
            "payer": "누가 결제했는지",
            "settlement_type": "사준 것인지 정산할 것인지",
            "category": "카테고리",
        }
        readable = [labels.get(field, field) for field in missing_fields]
        return ", ".join(readable) + " 정보를 알려주세요."

    def _build_title(self, text: str, category: str) -> str:
        if category == "외식":
            return "식사"
        if category == "카페":
            return "카페"
        if category == "교통":
            return "교통비"
        if category == "문화생활":
            return "문화생활"
        if category == "쇼핑":
            return "쇼핑"
        return text[:30]

    def _build_memo(self, event: ExpenseParseEvent) -> str:
        if event.settlement_type == "treated":
            return event.memo.replace("사줬어", "사줌").replace("사줬", "사줌")
        return event.memo
