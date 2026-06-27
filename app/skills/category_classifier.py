from __future__ import annotations

from app.skills.base import Skill
from app.skills.models import CategoryRequest, CategoryResult


class CategoryClassifierSkill(Skill[CategoryRequest, CategoryResult]):
    """Classify Korean spending text into a household-account category."""

    name = "category_classifier"

    CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
        "외식": ("밥", "식사", "술", "치킨", "고기", "삼겹살", "점심", "저녁", "회식"),
        "카페": ("커피", "카페", "아메리카노", "라떼", "디저트"),
        "교통": ("택시", "버스", "지하철", "기차", "주유", "대리"),
        "문화생활": ("영화", "게임", "공연", "전시", "콘서트", "뮤지컬"),
        "쇼핑": ("옷", "신발", "가방", "바지", "셔츠", "쇼핑"),
    }

    def run(self, data: CategoryRequest) -> CategoryResult:
        text = data.text.strip().lower()
        scores = {
            category: sum(1 for keyword in keywords if keyword in text)
            for category, keywords in self.CATEGORY_KEYWORDS.items()
        }
        matched = {category: score for category, score in scores.items() if score > 0}

        if not matched:
            return CategoryResult(
                category=None,
                confidence=0.0,
                needs_clarification=True,
                candidates=[],
            )

        best_score = max(matched.values())
        candidates = sorted(category for category, score in matched.items() if score == best_score)

        if len(candidates) > 1:
            return CategoryResult(
                category=None,
                confidence=0.5,
                needs_clarification=True,
                candidates=candidates,
            )

        total_score = sum(matched.values())
        confidence = best_score / total_score
        return CategoryResult(
            category=candidates[0],
            confidence=confidence,
            needs_clarification=False,
            candidates=candidates,
        )
