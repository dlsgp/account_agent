from datetime import date

import pytest

from app.services.ai_parser import ExpenseAnalysisService
from app.skills import CategoryClassifierSkill, ExpenseParserSkill, SettlementCalculatorSkill, SkillRegistry
from app.skills.models import CategoryRequest, ExpenseParseRequest, SettlementRequest


def test_expense_parser_returns_events_for_multi_event_sentence():
    result = ExpenseParserSkill().run(
        ExpenseParseRequest(
            text="오늘 시우랑 카페가서 만원 내가 결제하고, 시우가 저녁으로 고기 6만원 사줬어.",
            today=date(2026, 7, 3),
        )
    )

    assert result.clarification_required is False
    assert len(result.events) == 2
    assert result.events[0].total_amount == 10000
    assert result.events[0].payer == "me"
    assert result.events[0].participants == ["me", "시우"]
    assert result.events[0].settlement_type == "split"
    assert result.events[1].total_amount == 60000
    assert result.events[1].payer == "시우"
    assert result.events[1].settlement_type == "treated"


def test_analysis_service_calculates_multi_event_preview():
    result = ExpenseAnalysisService().analyze(
        "오늘 시우랑 카페가서 만원 내가 결제하고, 시우가 저녁으로 고기 6만원 사줬어.",
        today=date(2026, 7, 3),
    )

    assert result.clarification_required is False
    assert result.status == "ready"
    assert len(result.events) == 2

    cafe = result.events[0]
    assert cafe.title == "시우와 카페"
    assert cafe.category == "카페"
    assert cafe.total_amount == 10000
    assert cafe.payer == "me"
    assert cafe.payment_amount == 10000
    assert cafe.my_share == 5000
    assert cafe.receivable_amount == 5000
    assert cafe.payable_amount == 0

    dinner = result.events[1]
    assert dinner.title == "시우와 저녁 고기"
    assert dinner.category == "외식"
    assert dinner.total_amount == 60000
    assert dinner.payer == "시우"
    assert dinner.payment_amount == 0
    assert dinner.my_share == 0
    assert dinner.receivable_amount == 0
    assert dinner.payable_amount == 0
    assert dinner.settlement_type == "treated"


def test_taxi_paid_by_me_is_split():
    result = ExpenseAnalysisService().analyze("오늘 민수랑 택시 2만원 내가 냈어.", today=date(2026, 7, 3))

    assert result.clarification_required is False
    event = result.events[0]
    assert event.category == "교통"
    assert event.total_amount == 20000
    assert event.payment_amount == 20000
    assert event.my_share == 10000
    assert event.receivable_amount == 10000


def test_treated_coffee_without_amount_needs_clarification():
    result = ExpenseAnalysisService().analyze("오늘 지영이가 커피 사줬어.", today=date(2026, 7, 3))

    assert result.clarification_required is True
    assert "total_amount" in result.missing_fields


def test_plural_friends_without_count_needs_clarification():
    result = ExpenseAnalysisService().analyze("오늘 친구들이랑 술 마시고 9만원 내가 결제했어.", today=date(2026, 7, 3))

    assert result.clarification_required is True
    assert "people_count" in result.missing_fields


def test_other_person_paid_is_ambiguous():
    result = ExpenseAnalysisService().analyze("오늘 현우가 영화 3만원 결제했어.", today=date(2026, 7, 3))

    assert result.clarification_required is True
    assert "settlement_type" in result.missing_fields


def test_settlement_when_i_paid():
    result = SettlementCalculatorSkill().run(SettlementRequest(payment_amount=30000, people_count=2, paid_by_me=True))

    assert result.payment_amount == 30000
    assert result.my_share == 15000
    assert result.receivable_amount == 15000
    assert result.payable_amount == 0


def test_settlement_when_treated():
    result = SettlementCalculatorSkill().run(
        SettlementRequest(payment_amount=30000, people_count=2, paid_by_me=False, settlement_type="treated")
    )

    assert result.payment_amount == 0
    assert result.my_share == 0
    assert result.receivable_amount == 0
    assert result.payable_amount == 0


def test_settlement_rejects_invalid_people_count():
    with pytest.raises(ValueError):
        SettlementCalculatorSkill().run(SettlementRequest(payment_amount=30000, people_count=0, paid_by_me=True))


def test_category_classifier_classifies_restaurant_spending():
    result = CategoryClassifierSkill().run(CategoryRequest(text="오늘 친구랑 밥 먹고 치킨도 시켰어"))

    assert result.category == "외식"
    assert result.needs_clarification is False


def test_category_classifier_asks_when_unknown():
    result = CategoryClassifierSkill().run(CategoryRequest(text="오늘 뭔가 샀어"))

    assert result.category is None
    assert result.needs_clarification is True


def test_skill_registry_registers_and_finds_skills():
    registry = SkillRegistry()
    parser = ExpenseParserSkill()

    registry.register(parser)

    assert registry.names() == ["expense_parser"]
    assert registry.get("expense_parser") is parser
