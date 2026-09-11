from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence


class AIProvider(ABC):
    """Swap this implementation to change LLM/embedding vendors."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        raise NotImplementedError
