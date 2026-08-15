"""Shared 384-dimensional embedding generation (all-MiniLM-L6-v2).

Uses the HuggingFace Inference API to generate embeddings instead of running a local model.
Requires HF_API_KEY to be set in the environment.

Both user interest embeddings (Phase 2) and article embeddings (Phase 4)
go through `generate_embedding()` so they live in the same vector space.
"""
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.config import settings

EMBEDDING_DIMENSIONS = 384
API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

class HFApiError(Exception):
    pass

@retry(
    retry=retry_if_exception_type(HFApiError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
def generate_embedding(text: str) -> list[float]:
    """
    Generates a 384-dimensional vector for arbitrary text using HuggingFace API.
    """
    headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
    
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    
    if response.status_code != 200:
        # Raises error to trigger Tenacity retry (useful for 503 "model is loading" errors)
        raise HFApiError(f"HF API returned {response.status_code}: {response.text}")
        
    result = response.json()
    
    # HF Inference returns a list of floats (if single input) or list of lists (if batched)
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        embedding = result[0]
    else:
        embedding = result
        
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(embedding)}")

    return embedding



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
