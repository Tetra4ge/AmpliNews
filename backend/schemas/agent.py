from pydantic import BaseModel

class OpposingViewRequest(BaseModel):
    article_id: str

class OpposingViewResponse(BaseModel):
    article_id: str
    title: str
    bias: str
    bias_score: float
    credibility: float
    similarity: float


class DigestRequest(BaseModel):
    send_email: bool = True


class DigestTriggerResponse(BaseModel):
    user_id: str
    status: str
    echo_chamber_risk: float
    echo_chamber_detected: bool
    dominant_bias: str
    articles_selected_count: int
    contrarian_articles_count: int
    html_preview: str
    email_status: str

