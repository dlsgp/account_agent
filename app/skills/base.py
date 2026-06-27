from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Skill(ABC, Generic[InputT, OutputT]):
    """Common interface for independently executable agent skills."""

    name: str

    @abstractmethod
    def run(self, data: InputT) -> OutputT:
        """Execute the skill with validated input data."""
