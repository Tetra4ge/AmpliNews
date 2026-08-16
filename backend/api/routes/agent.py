import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from api.deps import get_db, get_current_user
from models.article import Article
from models.article_metadata import ArticleMetadata
from schemas.agent import OpposingViewRequest, OpposingViewResponse
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
