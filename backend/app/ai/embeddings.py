from __future__ import annotations

from typing import List, Sequence

from app.ai.provider import AIProvider


class EmbeddingService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def embed_query(self, text: str) -> List[float]:
        return self.provider.embed([text])[0]

    def embed_documents(self, texts: Sequence[str], batch_size: int = 64) -> List[List[float]]:
        vectors: List[List[float]] = []
        batch: List[str] = []
        for text in texts:
            batch.append(text)
            if len(batch) >= batch_size:
                vectors.extend(self.provider.embed(batch))
                batch = []
        if batch:
            vectors.extend(self.provider.embed(batch))
        return vectors
