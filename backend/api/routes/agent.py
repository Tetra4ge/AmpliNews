import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from api.deps import get_db, get_current_user
from models.article import Article
from models.article_metadata import ArticleMetadata
from schemas.agent import OpposingViewRequest, OpposingViewResponse, DigestRequest, DigestTriggerResponse
from api.routes.articles import get_bias_label

router = APIRouter()

@router.post("/opposing-view", response_model=OpposingViewResponse)
def get_opposing_view(
    payload: OpposingViewRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    try:
        source_id = uuid.UUID(payload.article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID format")

    # 1. Fetch source article
    source_result = db.execute(
        select(Article, ArticleMetadata)
        .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
        .where(Article.id == source_id)
    ).first()

    if not source_result:
        raise HTTPException(status_code=404, detail="Source article not found")

    source_article, source_metadata = source_result

    if source_article.article_embedding is None or source_metadata.bias_score is None:
        raise HTTPException(status_code=400, detail="Source article not fully enriched")

    # 2. Determine target bias range
    source_bias = source_metadata.bias_score
    if source_bias < 0:
        # Source is Left-leaning, we want > 0.2
        bias_filter = ArticleMetadata.bias_score > 0.2
    elif source_bias > 0:
        # Source is Right-leaning, we want < -0.1
        bias_filter = ArticleMetadata.bias_score < -0.1
    else:
        # Neutral source - just find something strongly biased
        bias_filter = (ArticleMetadata.bias_score > 0.3) | (ArticleMetadata.bias_score < -0.3)

    # 3. Vector Search for similar topic, but opposite bias
    similarity_threshold = 0.85

    # 1 - cosine_distance gives cosine similarity
    similarity_expr = 1 - Article.article_embedding.cosine_distance(source_article.article_embedding)

    opposing_result = db.execute(
        select(
            Article,
            ArticleMetadata,
            similarity_expr.label('similarity')
        )
        .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
        .where(Article.id != source_id)
        .where(similarity_expr > similarity_threshold)
        .where(bias_filter)
        .order_by(similarity_expr.desc(), ArticleMetadata.source_credibility.desc())
        .limit(1)
    ).first()

    if not opposing_result:
        raise HTTPException(status_code=404, detail="No opposing viewpoints found for this specific story yet.")

    opposing_article, opposing_metadata, similarity = opposing_result

    return OpposingViewResponse(
        article_id=str(opposing_article.id),
        title=opposing_article.title,
        bias=get_bias_label(opposing_metadata.bias_score),
        bias_score=opposing_metadata.bias_score,
        credibility=opposing_metadata.source_credibility,
        similarity=float(similarity)
    )


@router.post("/digest", response_model=DigestTriggerResponse)
def trigger_user_digest(
    payload: DigestRequest = DigestRequest(),
    current_user_id: str = Depends(get_current_user)
):
    """
    On-demand endpoint for a user to trigger their own Phase 9 LangGraph daily digest generation.
    Runs context retrieval, echo chamber risk analysis, standard/contrarian curation, and Groq synthesis.
    """
    from agent.graph import run_digest_agent
    from services.email import send_digest_email

    state = run_digest_agent(current_user_id)
    if state.get("status") == "error":
        raise HTTPException(
            status_code=500,
            detail=state.get("error_message") or "Failed to generate digest"
        )

    email_status = "skipped"
    if payload.send_email and state.get("final_email_html") and state.get("user_email"):
        res = send_digest_email(
            to_email=state["user_email"],
            html_content=state["final_email_html"],
            subject="Your AmpliNews Daily Digest 🗞️"
        )
        email_status = res.get("status", "unknown")

    return DigestTriggerResponse(
        user_id=current_user_id,
        status=state.get("status", "success"),
        echo_chamber_risk=state.get("echo_chamber_risk", 0.0),
        echo_chamber_detected=state.get("echo_chamber_detected", False),
        dominant_bias=state.get("dominant_bias", "Balanced"),
        articles_selected_count=len(state.get("selected_articles", [])),
        contrarian_articles_count=len(state.get("contrarian_articles", [])),
        html_preview=state.get("final_email_html", "")[:300] + "...",
        email_status=email_status
    )

