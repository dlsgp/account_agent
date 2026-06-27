from __future__ import annotations

import re
from datetime import date, timedelta

from app.skills.base import Skill
from app.skills.models import ExpenseParseRequest, ExpenseParseResult


class ExpenseParserSkill(Skill[ExpenseParseRequest, ExpenseParseResult]):
    """Extract structured expense facts from a Korean natural-language sentence."""

    name = "expense_parser"

    PARTICLE_PATTERN = re.compile(r"(이랑|랑|와|과|하고|한테|에게)$")
    PEOPLE_COUNT_PATTERN = re.compile(r"(\d+)\s*명")
    AMOUNT_PATTERN = re.compile(r"(\d+(?:,\d{3})*|\d+)\s*(만원|천원|원|만|천)?")
    NAME_CONTEXT_PATTERN = re.compile(r"([가-힣]{2,4})(?:이랑|랑|와|과|하고|한테|에게)")
    GENERIC_PARTICIPANTS = {"친구", "친구들", "동료", "가족", "사람들"}

    def run(self, data: ExpenseParseRequest) -> ExpenseParseResult:
        text = data.text.strip()
        today = data.today or date.today()

        parsed_date = self._parse_date(text, today)
        payment_amount = self._parse_amount(text)
        people_count = self._parse_people_count(text)
        paid_by_me = self._parse_paid_by_me(text)
        participants = self._parse_participants(text)

        if people_count is None and participants:
            people_count = len(participants) + 1

        missing_fields = []
        if parsed_date is None:
            missing_fields.append("date")
        if payment_amount is None:
            missing_fields.append("payment_amount")
        if people_count is None:
            missing_fields.append("people_count")
        if paid_by_me is None:
            missing_fields.append("paid_by_me")

        return ExpenseParseResult(
            date=parsed_date,
            payment_amount=payment_amount,
            people_count=people_count,
            paid_by_me=paid_by_me,
            participants=participants,
            memo=text,
            missing_fields=missing_fields,
        )

    def _parse_date(self, text: str, today: date) -> date | None:
        if "오늘" in text:
            return today
        if "어제" in text:
            return today - timedelta(days=1)
        if "그제" in text or "그저께" in text:
            return today - timedelta(days=2)

        month_day = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
        if month_day:
            month = int(month_day.group(1))
            day = int(month_day.group(2))
            return date(today.year, month, day)

        iso_date = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        if iso_date:
            return date(int(iso_date.group(1)), int(iso_date.group(2)), int(iso_date.group(3)))

        return None

    def _parse_amount(self, text: str) -> int | None:
        candidates: list[int] = []
        for match in self.AMOUNT_PATTERN.finditer(text):
            raw_number, unit = match.groups()
            number = int(raw_number.replace(",", ""))

            if unit in {"만원", "만"}:
                amount = number * 10000
            elif unit in {"천원", "천"}:
                amount = number * 1000
            elif unit == "원":
                amount = number
            else:
                continue

            if amount > 0:
                candidates.append(amount)

        return max(candidates) if candidates else None

    def _parse_people_count(self, text: str) -> int | None:
        match = self.PEOPLE_COUNT_PATTERN.search(text)
        if match:
            return int(match.group(1))

        if any(keyword in text for keyword in ("둘이", "둘이서", "친구랑", "친구와")):
            return 2

        return None

    def _parse_paid_by_me(self, text: str) -> bool | None:
        if any(keyword in text for keyword in ("내가 결제", "내가 냈", "제가 결제", "제가 냈", "내 카드")):
            return True
        if any(keyword in text for keyword in ("친구가 냈", "친구가 결제", "상대가 냈", "민수가 냈")):
            return False
        return None

    def _parse_participants(self, text: str) -> list[str]:
        names = []
        for match in self.NAME_CONTEXT_PATTERN.finditer(text):
            name = self.PARTICLE_PATTERN.sub("", match.group(1)).strip()
            if name and name not in {"내", "나", "저"}:
                names.append(name)

        if "친구랑" in text or "친구와" in text or "친구하고" in text:
            names.append("친구")

        deduped = []
        for name in names:
            if name not in deduped:
                deduped.append(name)
        return deduped
