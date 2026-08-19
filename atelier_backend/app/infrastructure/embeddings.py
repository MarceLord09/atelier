from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence

EMBEDDING_DIM = 1536
_TOKEN = re.compile(r"[a-záéíóúüñ0-9]+", re.IGNORECASE)


class HashingEmbedder:
    """Local 1536-d encoder so RAG works without a paid embedding API.

    Uses signed feature hashing of tokens, bigrams and char-trigrams.
    Swap this adapter for Gemini/OpenAI later; keep the same dimension
    or migrate the `brand_chunks.embedding vector(1536)` column.
    """

    name = "hashing-ngram-1536"

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [_vectorize(text) for text in texts]


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def as_pgvector(values: Sequence[float]) -> str:
    if len(values) != EMBEDDING_DIM:
        raise ValueError(f"Embedding must have {EMBEDDING_DIM} dimensions.")
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _vectorize(text: str) -> list[float]:
    vec = [0.0] * EMBEDDING_DIM
    normalized = text.casefold()
    tokens = _TOKEN.findall(normalized)
    features = list(tokens)
    features.extend(f"{left}_{right}" for left, right in zip(tokens, tokens[1:]))
    compact = re.sub(r"\s+", "", normalized)
    if len(compact) >= 3:
        features.extend(compact[index : index + 3] for index in range(len(compact) - 2))
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        number = int.from_bytes(digest, "little")
        index = number % EMBEDDING_DIM
        sign = 1.0 if (number >> 8) & 1 == 0 else -1.0
        vec[index] += sign
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]
