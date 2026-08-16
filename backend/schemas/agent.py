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
