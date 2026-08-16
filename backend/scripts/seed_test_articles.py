import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to sys.path so we can import from core/db/services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from models.article import Article
from services.enrichment import run_enrichment
from services.ingestion import generate_article_hash

async def seed_and_enrich():
    db = SessionLocal()
    
    # 1. Left-leaning article
    left_title = "Tax Cuts For The Wealthy Threaten Working Class Families"
    left_content = "The newly proposed tax cuts are a blatant giveaway to billionaires. If passed, this legislation will gut social safety nets and leave working class Americans struggling to pay for basic healthcare and education, while corporations post record profits."
    left_source = "Progressive Times"
    left_hash = generate_article_hash(left_title, left_source, datetime.utcnow())
    
    # 2. Right-leaning article
    right_title = "New Tax Cuts Will Spur Economic Growth and Job Creation"
    right_content = "The proposed tax cuts are exactly what our stalling economy needs. By allowing businesses to keep more of their hard-earned money, they will invest in hiring and expansion. Critics of the bill want to punish success and stifle the free market."
    right_source = "Conservative Daily"
    right_hash = generate_article_hash(right_title, right_source, datetime.utcnow())
    
    articles = [
        Article(
            title=left_title,
            content=left_content,
            source=left_source,
            url="https://example.com/left-tax",
            content_hash=left_hash,
            published_date=datetime.utcnow()
        ),
        Article(
            title=right_title,
            content=right_content,
            source=right_source,
            url="https://example.com/right-tax",
            content_hash=right_hash,
            published_date=datetime.utcnow()
        )
    ]
    
    for a in articles:
        # Avoid duplicate inserts
        if not db.query(Article).filter(Article.content_hash == a.content_hash).first():
            db.add(a)
            
    db.commit()
    print("Test articles inserted into database.")
    print("Running enrichment pipeline to generate embeddings and bias scores (this will take a few seconds)...")
    
    # Run enrichment so they get their embeddings and metadata
    summary = await run_enrichment(db)
    print(f"Enrichment complete! Summary: {summary}")
    db.close()
    
if __name__ == "__main__":
    asyncio.run(seed_and_enrich())
