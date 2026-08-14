"""Shared 384-dimensional embedding generation (all-MiniLM-L6-v2).

Uses a locally-loaded `sentence-transformers` model rather than HuggingFace's
hosted Inference API: `api-inference.huggingface.co` (the endpoint this
module originally called) has been decommissioned by HuggingFace and no
longer resolves at all, which made every embedding silently fall back to a
zero-vector. Running the model locally removes that external dependency and
its associated latency/rate-limit/cost entirely - it also matches the
Phase 4 spec's explicitly sanctioned "local embeddings" option.

Both user interest embeddings (Phase 2) and article embeddings (Phase 4)
go through `generate_embedding()` so they live in the same vector space.
"""
from sentence_transformers import SentenceTransformer

EMBEDDING_DIMENSIONS = 384
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def generate_embedding(text: str) -> list[float]:
    """
    Generates a 384-dimensional vector for arbitrary text using a local
    all-MiniLM-L6-v2 model.
    """
    try:
        vector = _get_model().encode(text)
        embedding = vector.tolist()

        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError(f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(embedding)}")

        return embedding
    except Exception as e:
        print(f"Warning: Failed to generate embedding locally: {e}")
        # Fallback to a zero-vector so callers never crash on a model hiccup.
        return [0.0] * EMBEDDING_DIMENSIONS


def generate_user_embedding(topics: list[str]) -> list[float]:
    """
    Generates a 384-dimensional vector for the user's selected topics.
    """
    prompt = f"A reader interested in: {', '.join(topics)}"
    return generate_embedding(prompt)


def generate_article_embedding(title: str, content: str) -> list[float]:
    """
    Generates a 384-dimensional vector for an article's title + content,
    per the Phase 4 lazy embedding generation spec.
    """
    return generate_embedding(f"{title}. {content}")
