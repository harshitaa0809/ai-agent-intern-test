import re
from dataclasses import dataclass

from .models import DocumentChunk


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float


class KnowledgeRetriever:
    """
    Retrieve relevant knowledge-base chunks while respecting
    document authority and status.
    """

    def __init__(self, chunks: list[DocumentChunk]):
        self.chunks = chunks

    def search(
        self,
        query: str,
        top_k: int = 5,
        include_internal: bool = False,
    ) -> list[RetrievalResult]:
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        candidates = []

        for chunk in self.chunks:
            if not self._is_usable_source(chunk, include_internal):
                continue

            score = self._score_chunk(query, query_tokens, chunk)

            if score > 0:
                candidates.append(
                    RetrievalResult(
                        chunk=chunk,
                        score=score,
                    )
                )

        candidates.sort(
            key=lambda result: (
                result.score,
                result.chunk.metadata.get("effective_date", ""),
            ),
            reverse=True,
        )

        return candidates[:top_k]

    @staticmethod
    def _is_usable_source(
        chunk: DocumentChunk,
        include_internal: bool,
    ) -> bool:
        metadata = chunk.metadata

        # Draft/unapproved material is never authoritative.
        if metadata.get("status") == "draft":
            return False

        # Documents explicitly marked as having no authority
        # must not be used as customer policy.
        if metadata.get("policy_authority") != "official":
            return False

        # Superseded documents should not be used when an active
        # authoritative version exists.
        if metadata.get("status") == "superseded":
            return False

        # Internal documents are useful for agent behavior and
        # handoff rules, but should not normally be treated as
        # customer-facing policy.
        if metadata.get("audience") == "internal" and not include_internal:
            return False

        return True

    def _score_chunk(
        self,
        query: str,
        query_tokens: set[str],
        chunk: DocumentChunk,
    ) -> float:
        content = self._normalize(chunk.content)
        heading = self._normalize(chunk.heading)
        title = self._normalize(chunk.title)
        normalized_query = self._normalize(query)

        score = 0.0

        # Exact phrase match is strong evidence of relevance.
        if normalized_query in content:
            score += 8.0

        if normalized_query in heading:
            score += 10.0

        # Token overlap.
        content_tokens = self._tokenize(content)
        heading_tokens = self._tokenize(heading)
        title_tokens = self._tokenize(title)

        for token in query_tokens:
            if token in content_tokens:
                score += 1.0

            if token in heading_tokens:
                score += 3.0

            if token in title_tokens:
                score += 2.0

        # Stronger boost for active official sources.
        if chunk.metadata.get("status") == "active":
            score += 2.0

        if chunk.metadata.get("policy_authority") == "official":
            score += 2.0

        return score

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        normalized = cls._normalize(text)

        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "be",
            "can",
            "do",
            "does",
            "for",
            "how",
            "i",
            "in",
            "is",
            "it",
            "my",
            "of",
            "on",
            "or",
            "the",
            "to",
            "what",
            "when",
            "where",
            "with",
        }

        return {
            token
            for token in normalized.split()
            if token not in stop_words and len(token) > 1
        }