"""System prompts and structured-output schemas for LLM queries."""
from pydantic import BaseModel, Field


class ArticleAnalysis(BaseModel):
    """Structured output for the Groq bias/sentiment/credibility pass."""

    bias_score: float = Field(
        ..., ge=-1.0, le=1.0,
        description="-1.0 = Extreme Left/Liberal, +1.0 = Extreme Right/Conservative, 0.0 = neutral",
    )
    sentiment: str = Field(..., description="One of: Positive, Negative, Neutral, Alarmist")
    source_credibility: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated journalistic credibility of the source"
    )
    topic: str = Field(..., description="Primary topic/category of the article")


ARTICLE_ANALYSIS_SYSTEM_PROMPT = """You are a deterministic news analysis engine used inside an \
automated pipeline. You will be given a news article's title and content. Analyze it and return \
ONLY a JSON object with exactly these fields:

- "bias_score": a float from -1.0 to 1.0. -1.0 means extreme left/liberal political bias, \
+1.0 means extreme right/conservative political bias, 0.0 means perfectly neutral/balanced \
reporting. Base this strictly on the framing, word choice, and selection of facts in the text \
itself - not on your prior knowledge of the source's typical leaning.
- "sentiment": one of "Positive", "Negative", "Neutral", or "Alarmist".
- "source_credibility": a float from 0.0 to 1.0 estimating journalistic credibility based on the \
source name and the article's adherence to journalistic standards (factual claims, absence of \
sensationalism, balanced sourcing).
- "topic": a short single-word-or-two topic label (e.g. "Politics", "Technology", "Business", \
"Health", "Science").

Be consistent and deterministic. Do not include any explanation, markdown, or text outside the \
JSON object."""


def build_article_analysis_messages(title: str, content: str) -> list[dict]:
    """Builds the Groq chat messages for a single article analysis call."""
    return [
        {"role": "system", "content": ARTICLE_ANALYSIS_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Title: {title}\n\nContent: {content}",
        },
    ]
