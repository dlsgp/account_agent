from __future__ import annotations

import json
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.expense import ExpenseAnalyzeResponse, ExpensePreview, ParticipantPreview
from app.services.settlement import calculate_settlement
from app.skills import CategoryClassifierSkill, ExpenseParserSkill
from app.skills.models import CategoryRequest, ExpenseParseRequest


class ExpenseAnalysisService:
    def __init__(self) -> None:
        self.expense_parser = ExpenseParserSkill()
        self.category_classifier = CategoryClassifierSkill()

    def analyze(self, text: str, today: date | None = None) -> ExpenseAnalyzeResponse:
        if settings.openai_api_key:
            llm_result = self._analyze_with_llm(text)
            if llm_result is not None:
                return llm_result
        return self._analyze_with_skills(text, today=today)

    def _analyze_with_skills(self, text: str, today: date | None = None) -> ExpenseAnalyzeResponse:
        parsed = self.expense_parser.run(ExpenseParseRequest(text=text, today=today))
        categorized = self.category_classifier.run(CategoryRequest(text=text))

        missing_fields = list(parsed.missing_fields)
        if categorized.needs_clarification:
            missing_fields.append("category")

        if missing_fields:
            return ExpenseAnalyzeResponse(
                status="needs_clarification",
                missing_fields=missing_fields,
                question=self._build_question(missing_fields),
            )

        assert parsed.date is not None
        assert parsed.payment_amount is not None
        assert parsed.people_count is not None
        assert parsed.paid_by_me is not None
        assert categorized.category is not None

        settlement = calculate_settlement(parsed.payment_amount, parsed.people_count, parsed.paid_by_me)
        participants = self._build_participants(parsed.participants, settlement.receivable_amount)

        preview = ExpensePreview(
            date=parsed.date,
            title=self._build_title(text, categorized.category),
            category=categorized.category,
            payment_amount=settlement.payment_amount,
            my_share=settlement.my_share,
            people_count=parsed.people_count,
            paid_by_me=parsed.paid_by_me,
            receivable_amount=settlement.receivable_amount,
            payable_amount=settlement.payable_amount,
            memo=parsed.memo,
            raw_input=text,
            participants=participants,
        )
        return ExpenseAnalyzeResponse(status="ready", preview=preview)

    def _analyze_with_llm(self, text: str) -> ExpenseAnalyzeResponse | None:
        try:
            from openai import OpenAI
        except ImportError:
            return None

        client = OpenAI(api_key=settings.openai_api_key)
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract Korean household expense facts as JSON only. "
                            "Fields: date,title,category,payment_amount,people_count,"
                            "paid_by_me,participants,memo,missing_fields."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
            payload = json.loads(response.choices[0].message.content or "{}")
            return self._response_from_llm_payload(text, payload)
        except Exception:
            return None

    def _response_from_llm_payload(self, text: str, payload: dict[str, Any]) -> ExpenseAnalyzeResponse:
        missing_fields = list(payload.get("missing_fields") or [])
        required = ["date", "payment_amount", "people_count", "paid_by_me", "category"]
        for field in required:
            if payload.get(field) in (None, "") and field not in missing_fields:
                missing_fields.append(field)

        if missing_fields:
            return ExpenseAnalyzeResponse(
                status="needs_clarification",
                missing_fields=missing_fields,
                question=self._build_question(missing_fields),
            )

        settlement = calculate_settlement(
            int(payload["payment_amount"]),
            int(payload["people_count"]),
            bool(payload["paid_by_me"]),
        )
        participant_names = [str(name) for name in payload.get("participants") or []]
        try:
            preview = ExpensePreview(
                date=payload["date"],
                title=str(payload.get("title") or payload["category"]),
                category=str(payload["category"]),
                payment_amount=settlement.payment_amount,
                my_share=settlement.my_share,
                people_count=int(payload["people_count"]),
                paid_by_me=bool(payload["paid_by_me"]),
                receivable_amount=settlement.receivable_amount,
                payable_amount=settlement.payable_amount,
                memo=str(payload.get("memo") or text),
                raw_input=text,
                participants=self._build_participants(participant_names, settlement.receivable_amount),
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            return self._analyze_with_skills(text)

        return ExpenseAnalyzeResponse(status="ready", preview=preview)

    def _build_participants(self, names: list[str], receivable_amount: int) -> list[ParticipantPreview]:
        if receivable_amount <= 0 or not names:
            return []
        base_amount = receivable_amount // len(names)
        participants = []
        for index, name in enumerate(names):
            amount = base_amount
            if index == len(names) - 1:
                amount = receivable_amount - (base_amount * (len(names) - 1))
            participants.append(ParticipantPreview(name=name, receivable_amount=amount))
        return participants

    def _build_question(self, missing_fields: list[str]) -> str:
        labels = {
            "date": "날짜",
            "payment_amount": "총 금액",
            "people_count": "함께한 인원 수",
            "paid_by_me": "누가 결제했는지",
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
