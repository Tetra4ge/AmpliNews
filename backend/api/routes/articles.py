import math
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from api.deps import get_db, get_current_user
from models.article import Article
from models.user_profile import UserProfile
from models.article_metadata import ArticleMetadata

router = APIRouter()

def get_bias_label(score: float) -> str:
    if score < -0.3:
        return "Left"
    elif score > 0.3:
        return "Right"
    return "Center"


@router.get("/feed")
def get_personalized_feed(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user),
    limit: int = 10,
    days_back: int = 2
):
    # Fetch User Profile to get interest_embedding
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user_id).first()
    
    if not user_profile or not user_profile.interest_embedding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile has no interests defined. Please complete onboarding."
        )
        
    user_embedding = user_profile.interest_embedding
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    
    # Intelligent News Feed API:
    # Vector Similarity Search using pgvector's <=> (cosine distance)
    # This leverages the HNSW index on the database!
    similarity = Article.article_embedding.cosine_distance(user_embedding).label('distance')
    
    # The optimized JOIN query that fetches articles, metadata, and calculates distance simultaneously
    query = (
        select(Article, ArticleMetadata, similarity)
        .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
        .where(Article.published_date > cutoff_date)
        .order_by(similarity)
        .limit(limit)
    )
    
    results = db.execute(query).all()
    
    feed = []
    for article, metadata, distance in results:
        # Math Transform: Cosine Similarity = 1 - Cosine Distance
        # If pgvector distance is exactly 0, similarity is 100%.
        match_percentage = round((1 - float(distance)) * 100, 1)
        
        feed.append({
            "article_id": str(article.id),
            "title": article.title,
            "source": article.source,
            "url": article.url,
            "published_date": article.published_date.isoformat() if article.published_date else None,
            "match_percentage": match_percentage,
            "bias": get_bias_label(metadata.bias_score),
            "bias_score": metadata.bias_score,
            "credibility": metadata.source_credibility,
            "reasoning": "Matches your interest profile."
        })
        
    return {"feed": feed}

@router.get("/{article_id}")
def get_article(
    article_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    Fetches the full article content and metadata for the reading view.
    """
    query = (
        select(Article, ArticleMetadata)
        .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
        .where(Article.id == article_id)
    )
    result = db.execute(query).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found."
        )
        
    article, metadata = result
    
    return {
        "article_id": str(article.id),
        "title": article.title,
        "content": article.content,
        "url": article.url,
        "source": article.source,
        "published_date": article.published_date.isoformat() if article.published_date else None,
        "metadata": {
            "bias_score": metadata.bias_score,
            "bias": get_bias_label(metadata.bias_score),
            "sentiment": metadata.sentiment,
            "source_credibility": metadata.source_credibility,
            "topic": metadata.topic
        }
    }
