"""Phase 4: Groq-based bias/sentiment/credibility analysis for articles."""
import json

from groq import Groq
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.config import settings
from llm.prompts import ArticleAnalysis, build_article_analysis_messages

# Fast, cheap Llama model - good enough for structured classification and
# keeps the enrichment loop well within the "10 articles < 15s" budget.
GROQ_MODEL = "llama-3.1-8b-instant"

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


class GroqRateLimitError(Exception):
    """Raised when Groq returns 429 - retried with exponential backoff."""


def _is_rate_limit_error(exc: BaseException) -> bool:
    status_code = getattr(exc, "status_code", None)
    return status_code == 429


@retry(
    retry=retry_if_exception_type(GroqRateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
def analyze_article(title: str, content: str) -> ArticleAnalysis:
    """Calls Groq to classify bias/sentiment/credibility/topic for one article.

    Retries with exponential backoff on HTTP 429 (rate limit). Any other
    failure (malformed JSON, validation error, non-429 API error) propagates
    immediately so the caller can skip the article rather than retry forever.
    """
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=build_article_analysis_messages(title, content),
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=200,
        )
    except Exception as exc:
        if _is_rate_limit_error(exc):
            raise GroqRateLimitError(str(exc)) from exc
        raise

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        return ArticleAnalysis(**parsed)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise ValueError(f"Groq returned an unparsable analysis: {raw!r}") from exc
