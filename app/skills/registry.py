from __future__ import annotations

from app.skills.base import Skill


class SkillRegistry:
    """Small registry so new skills can be added without changing callers."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise KeyError(f"Skill is not registered: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._skills)
