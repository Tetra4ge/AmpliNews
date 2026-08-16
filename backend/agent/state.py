"""Phase 9: LangGraph State Definition for Daily Digest Generation."""
from typing import TypedDict, List, Dict, Any, Optional


class DigestState(TypedDict):
    """State schema passed through the LangGraph digest generation workflow."""

    user_id: str
    user_email: Optional[str]
    reading_history: List[Dict[str, Any]]
    echo_chamber_risk: float
    echo_chamber_detected: bool
    dominant_bias: str  # Left, Right, Center, or Balanced
    top_topic: Optional[str]
    selected_articles: List[Dict[str, Any]]
    contrarian_articles: List[Dict[str, Any]]
    final_email_html: str
    status: str  # success / error / pending
    error_message: Optional[str]
