from datetime import date

import pytest

from app.skills import CategoryClassifierSkill, ExpenseParserSkill, SettlementCalculatorSkill, SkillRegistry
from app.skills.models import CategoryRequest, ExpenseParseRequest, SettlementRequest


def test_expense_parser_extracts_core_fields_from_korean_sentence():
    skill = ExpenseParserSkill()

    result = skill.run(
        ExpenseParseRequest(
            text="오늘 친구랑 밥을 먹어서 총 3만원이 나왔는데 내가 결제했어.",
            today=date(2026, 6, 27),
        )
    )

    assert result.date == date(2026, 6, 27)
    assert result.payment_amount == 30000
    assert result.people_count == 2
    assert result.paid_by_me is True
    assert result.participants == ["친구"]
    assert result.missing_fields == []


def test_expense_parser_reports_missing_amount():
    skill = ExpenseParserSkill()

    result = skill.run(
        ExpenseParseRequest(
            text="어제 민수랑 택시 탔고 내가 냈어.",
            today=date(2026, 6, 27),
        )
    )

    assert result.date == date(2026, 6, 26)
    assert result.payment_amount is None
    assert result.people_count == 2
    assert result.paid_by_me is True
    assert "payment_amount" in result.missing_fields


def test_settlement_when_i_paid():
    skill = SettlementCalculatorSkill()

    result = skill.run(SettlementRequest(payment_amount=30000, people_count=2, paid_by_me=True))

    assert result.payment_amount == 30000
    assert result.my_share == 15000
    assert result.receivable_amount == 15000
    assert result.payable_amount == 0


def test_settlement_when_someone_else_paid():
    skill = SettlementCalculatorSkill()

    result = skill.run(SettlementRequest(payment_amount=30000, people_count=2, paid_by_me=False))

    assert result.my_share == 15000
    assert result.receivable_amount == 0
    assert result.payable_amount == 15000


def test_settlement_rejects_invalid_people_count():
    skill = SettlementCalculatorSkill()

    with pytest.raises(ValueError):
        skill.run(SettlementRequest(payment_amount=30000, people_count=0, paid_by_me=True))


def test_category_classifier_classifies_restaurant_spending():
    skill = CategoryClassifierSkill()

    result = skill.run(CategoryRequest(text="오늘 친구랑 밥 먹고 치킨도 시켰어"))

    assert result.category == "외식"
    assert result.needs_clarification is False


def test_category_classifier_asks_when_unknown():
    skill = CategoryClassifierSkill()

    result = skill.run(CategoryRequest(text="오늘 뭔가 샀어"))

    assert result.category is None
    assert result.needs_clarification is True


def test_skill_registry_registers_and_finds_skills():
    registry = SkillRegistry()
    parser = ExpenseParserSkill()

    registry.register(parser)

    assert registry.names() == ["expense_parser"]
    assert registry.get("expense_parser") is parser
