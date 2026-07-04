from __future__ import annotations

import re
from datetime import date, timedelta

from app.skills.base import Skill
from app.skills.models import ExpenseParseEvent, ExpenseParseRequest, ExpenseParseResult


class ExpenseParserSkill(Skill[ExpenseParseRequest, ExpenseParseResult]):
    """Extract one or more expense events from a Korean natural-language sentence."""

    name = "expense_parser"

    AMOUNT_PATTERN = re.compile(r"(\d+(?:,\d{3})*|\d+)\s*(만원|천원|원|만|천)")
    NAME_WITH_PATTERN = re.compile(r"([가-힣]{2,4})(?:이랑|랑|와|과|하고)")
    PAYER_PATTERN = re.compile(r"([가-힣]{2,4}?)(?:이|가).*?(사줬|내줬|계산해줬|결제했|냈)")
    PEOPLE_COUNT_PATTERN = re.compile(r"(\d+)\s*명")
    DATE_PATTERNS = ("오늘", "어제", "그제", "그저께")

    def run(self, data: ExpenseParseRequest) -> ExpenseParseResult:
        text = data.text.strip()
        today = data.today or date.today()
        parsed_date = self._parse_date(text, today)
        context_participants = self._parse_participants(text)
        chunks = self._split_events(text)
        events = [
            self._parse_event(chunk, parsed_date, context_participants)
            for chunk in chunks
            if chunk.strip()
        ]

        missing_fields = sorted({field for event in events for field in event.missing_fields})
        return ExpenseParseResult(
            clarification_required=bool(missing_fields),
            events=events,
            missing_fields=missing_fields,
        )

    def _split_events(self, text: str) -> list[str]:
        protected = text.replace("그리고", ",")
        chunks = re.split(r",|\s+하고\s+", protected)
        return [chunk.strip(" .") for chunk in chunks if chunk.strip(" .")]

    def _parse_event(
        self,
        chunk: str,
        parsed_date: date | None,
        context_participants: list[str],
    ) -> ExpenseParseEvent:
        amount = self._parse_amount(chunk)
        participants = self._merge_participants(context_participants, self._parse_participants(chunk))
        payer, settlement_type, ambiguous = self._parse_payer(chunk)
        people_count = self._parse_people_count(chunk, participants)
        title = self._build_title(chunk, participants)
        missing_fields = []

        if parsed_date is None:
            missing_fields.append("date")
        if amount is None:
            missing_fields.append("total_amount")
        if people_count is None:
            missing_fields.append("people_count")
        if payer is None:
            missing_fields.append("payer")
        if ambiguous:
            missing_fields.append("settlement_type")

        return ExpenseParseEvent(
            date=parsed_date,
            title=title,
            total_amount=amount,
            payer=payer,
            participants=self._participants_with_me(participants),
            people_count=people_count,
            settlement_type=settlement_type,
            memo=chunk,
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
            return date(today.year, int(month_day.group(1)), int(month_day.group(2)))

        iso_date = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        if iso_date:
            return date(int(iso_date.group(1)), int(iso_date.group(2)), int(iso_date.group(3)))

        return None

    def _parse_amount(self, text: str) -> int | None:
        if re.search(r"(?<!\d)만원", text):
            return 10000
        if re.search(r"(?<!\d)천원", text):
            return 1000
        match = self.AMOUNT_PATTERN.search(text)
        if not match:
            return None
        raw_number, unit = match.groups()
        number = int(raw_number.replace(",", ""))
        if unit in {"만원", "만"}:
            return number * 10000
        if unit in {"천원", "천"}:
            return number * 1000
        return number

    def _parse_people_count(self, text: str, participants: list[str]) -> int | None:
        match = self.PEOPLE_COUNT_PATTERN.search(text)
        if match:
            return int(match.group(1))
        if "친구들이랑" in text or "친구들" in text:
            return None
        if participants:
            return len(self._participants_with_me(participants))
        return None

    def _parse_payer(self, text: str) -> tuple[str | None, str | None, bool]:
        if any(keyword in text for keyword in ("내가 결제", "내가 냈", "제가 결제", "제가 냈")):
            return "me", "split", False

        payer_match = self.PAYER_PATTERN.search(text)
        if not payer_match:
            return None, None, False

        payer = self._normalize_name(payer_match.group(1))
        action = payer_match.group(2)
        if action in {"사줬", "내줬", "계산해줬"}:
            return payer, "treated", False
        if action in {"결제했", "냈"}:
            return payer, None, True
        return None, None, False

    def _parse_participants(self, text: str) -> list[str]:
        names = [self._normalize_name(match.group(1)) for match in self.NAME_WITH_PATTERN.finditer(text)]
        payer_match = self.PAYER_PATTERN.search(text)
        if payer_match:
            names.append(self._normalize_name(payer_match.group(1)))
        if "친구" in text:
            names.append("친구")
        excluded = {"나", "내", "저", "제가", "만원", "천원", "결제", "카페", "커피", "저녁", "고기", "영화", "택시", "술"}
        return self._dedupe([name for name in names if name not in excluded])

    def _merge_participants(self, first: list[str], second: list[str]) -> list[str]:
        return self._dedupe(first + second)

    def _participants_with_me(self, participants: list[str]) -> list[str]:
        return self._dedupe(["me"] + participants)

    def _normalize_name(self, name: str) -> str:
        return re.sub(r"(이|가)$", "", name.strip())

    def _build_title(self, text: str, participants: list[str]) -> str:
        subject = f"{participants[0]}와 " if participants else ""
        if "카페" in text or "커피" in text:
            return subject + ("카페" if "카페" in text else "커피")
        if "고기" in text:
            return subject + ("저녁 고기" if "저녁" in text else "고기")
        if "택시" in text:
            return subject + "택시"
        if "술" in text:
            return subject + "술"
        if "영화" in text:
            return subject + "영화"
        return subject + "지출"

    def _dedupe(self, values: list[str]) -> list[str]:
        result = []
        for value in values:
            if value and value not in result:
                result.append(value)
        return result
