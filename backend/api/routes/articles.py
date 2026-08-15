from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from api.deps import get_db, get_current_user
from models.article import Article
from models.user_profile import UserProfile
from models.article_metadata import ArticleMetadata

router = APIRouter()

@router.get("/feed")
def get_personalized_feed(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    # Fetch User Profile to get interest_embedding
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user_id).first()
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete onboarding."
        )
        
    user_embedding = user_profile.interest_embedding
    
    if user_embedding is None:
        # Fallback: Chronological order if user has no interests defined yet
        articles = db.query(Article).order_by(Article.published_date.desc()).offset(offset).limit(limit).all()
    else:
        # Intelligent News Feed API:
        # Vector Similarity Search using pgvector's <=> (cosine distance)
        # Orders articles by how semantically similar they are to the user's interest_embedding
        articles = db.query(Article).order_by(
            Article.article_embedding.cosine_distance(user_embedding)
        ).offset(offset).limit(limit).all()
        
    feed = []
    for article in articles:
        # Fetch associated AI analysis metadata for the frontend
        metadata = db.query(ArticleMetadata).filter(ArticleMetadata.article_id == article.id).first()
        
        feed.append({
            "id": str(article.id),
            "title": article.title,
            "content": article.content,
            "source": article.source,
            "url": article.url,
            "published_date": article.published_date.isoformat() if article.published_date else None,
            "metadata": {
                "bias_score": metadata.bias_score,
                "sentiment": metadata.sentiment,
                "source_credibility": metadata.source_credibility,
                "topic": metadata.topic
            } if metadata else None
        })
        
    return {"articles": feed}
