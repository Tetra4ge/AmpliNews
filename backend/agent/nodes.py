"""Phase 9: LangGraph Agent Nodes for AmpliNews Daily Digest Machine."""
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from db.session import SessionLocal
from models.user_profile import UserProfile
from models.reading_history import ReadingHistory
from models.article import Article
from models.article_metadata import ArticleMetadata
from agent.state import DigestState
from core.config import settings

logger = logging.getLogger(__name__)


def retrieve_context_node(state: DigestState) -> DigestState:
    """
    Node 1: RetrieveContextNode
    Fetches the user's profile and last 7 days of reading history from CockroachDB.
    """
    user_id_str = state.get("user_id")
    if not user_id_str:
        state["status"] = "error"
        state["error_message"] = "Missing user_id in state"
        return state

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        state["status"] = "error"
        state["error_message"] = f"Invalid user_id format: {user_id_str}"
        return state

    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
        if not profile:
            state["status"] = "error"
            state["error_message"] = f"User profile not found for user_id {user_id_str}"
            return state

        # Fetch last 7 days of reading history
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        history_query = (
            select(ReadingHistory, Article, ArticleMetadata)
            .join(Article, ReadingHistory.article_id == Article.id)
            .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
            .where(ReadingHistory.user_id == user_uuid)
            .where(ReadingHistory.timestamp >= cutoff)
            .order_by(ReadingHistory.timestamp.desc())
        )

        results = db.execute(history_query).all()

        history_items: List[Dict[str, Any]] = []
        for rh, art, meta in results:
            history_items.append({
                "history_id": str(rh.id),
                "article_id": str(art.id),
                "title": art.title,
                "source": art.source,
                "topic": meta.topic or "General",
                "bias_score": meta.bias_score if meta.bias_score is not None else 0.0,
                "read_duration": rh.read_duration_seconds or 0,
                "liked": rh.liked or False,
                "rejected_biased": rh.rejected_biased or False,
                "timestamp": rh.timestamp.isoformat() if rh.timestamp else None,
            })

        state["reading_history"] = history_items
        # Fallback email if user profile has no explicit email field
        state["user_email"] = getattr(profile, "email", None) or settings.AWS_SES_SENDER_EMAIL
        state["status"] = "pending"
        logger.info(f"[RetrieveContextNode] Retrieved {len(history_items)} history items for user {user_id_str}")

    except Exception as e:
        logger.error(f"[RetrieveContextNode] Error fetching context: {e}", exc_info=True)
        state["status"] = "error"
        state["error_message"] = str(e)
    finally:
        db.close()

    return state


def analyze_bias_node(state: DigestState) -> DigestState:
    """
    Node 2: AnalyzeBiasNode
    Calculates echo chamber risk based on user's recent reading history.
    Detects bias skew and low variance.
    """
    history = state.get("reading_history", [])
    if not history:
        # Default fallback for new/inactive users
        state["echo_chamber_risk"] = 0.0
        state["echo_chamber_detected"] = False
        state["dominant_bias"] = "Balanced"
        state["top_topic"] = "Politics"
        return state

    bias_scores = [item["bias_score"] for item in history if item.get("bias_score") is not None]
    topics = [item["topic"] for item in history if item.get("topic")]

    # Find top read topic
    top_topic = None
    if topics:
        topic_counts: Dict[str, int] = {}
        for t in topics:
            topic_counts[t] = topic_counts.get(t, 0) + 1
        top_topic = max(topic_counts, key=topic_counts.get)
    state["top_topic"] = top_topic or "Politics"

    if not bias_scores:
        state["echo_chamber_risk"] = 0.0
        state["echo_chamber_detected"] = False
        state["dominant_bias"] = "Balanced"
        return state

    # Statistical calculation
    avg_bias = sum(bias_scores) / len(bias_scores)
    variance = sum((b - avg_bias) ** 2 for b in bias_scores) / len(bias_scores)
    std_dev = math.sqrt(variance)

    # Determine dominant bias label
    if avg_bias < -0.3:
        dominant_bias = "Left"
    elif avg_bias > 0.3:
        dominant_bias = "Right"
    else:
        dominant_bias = "Center"

    # Echo Chamber Risk formula:
    # High risk if high mean skew AND low standard deviation (narrow spectrum)
    # or if > 70% of reads are heavily biased to one side.
    skew_component = abs(avg_bias)  # 0 to 1
    narrowness_component = max(0.0, 1.0 - (std_dev * 2.0))  # 1 when std_dev close to 0

    echo_chamber_risk = round(0.6 * skew_component + 0.4 * narrowness_component, 2)
    # Ensure range [0.0, 1.0]
    echo_chamber_risk = max(0.0, min(1.0, echo_chamber_risk))

    # Threshold for perspective intervention
    echo_chamber_detected = echo_chamber_risk >= 0.60


    state["echo_chamber_risk"] = echo_chamber_risk
    state["echo_chamber_detected"] = echo_chamber_detected
    state["dominant_bias"] = dominant_bias if echo_chamber_detected else "Balanced"

    logger.info(
        f"[AnalyzeBiasNode] User {state.get('user_id')}: avg_bias={avg_bias:.2f}, "
        f"std_dev={std_dev:.2f}, risk={echo_chamber_risk}, detected={echo_chamber_detected}"
    )

    return state


def curate_standard_node(state: DigestState) -> DigestState:
    """
    Node 3: CurateStandardNode
    Performs vector similarity search against user's interest_embedding in CockroachDB
    to retrieve 5 personalized articles for the daily digest.
    """
    user_id_str = state.get("user_id")
    history = state.get("reading_history", [])
    read_article_ids = {h["article_id"] for h in history if "article_id" in h}

    db = SessionLocal()
    try:
        user_uuid = uuid.UUID(user_id_str)
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()

        if not profile or profile.interest_embedding is None:
            state["selected_articles"] = []
            return state

        user_embedding = profile.interest_embedding
        similarity = Article.article_embedding.cosine_distance(user_embedding).label("distance")

        # Query top articles with valid embeddings by vector distance
        query = (
            select(Article, ArticleMetadata, similarity)
            .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
            .where(Article.article_embedding.isnot(None))
            .order_by(similarity)
            .limit(15)
        )

        results = db.execute(query).all()

        curated: List[Dict[str, Any]] = []
        for article, metadata, distance in results:
            art_id_str = str(article.id)
            # Skip articles already read recently
            if art_id_str in read_article_ids:
                continue

            match_pct = round((1 - float(distance)) * 100, 1) if distance is not None else 85.0
            bias_val = metadata.bias_score or 0.0

            if bias_val < -0.3:
                bias_label = "Left"
            elif bias_val > 0.3:
                bias_label = "Right"
            else:
                bias_label = "Center"

            content_summary = (article.content[:200] + "...") if article.content and len(article.content) > 200 else (article.content or article.title)

            curated.append({
                "article_id": art_id_str,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "content_summary": content_summary,
                "match_percentage": match_pct,
                "bias": bias_label,
                "bias_score": bias_val,
                "credibility": metadata.source_credibility or 0.8,
                "topic": metadata.topic or "General",
            })

            if len(curated) >= 5:
                break

        state["selected_articles"] = curated
        logger.info(f"[CurateStandardNode] Curated {len(curated)} standard articles for user {user_id_str}")

    except Exception as e:
        logger.error(f"[CurateStandardNode] Error curating articles: {e}", exc_info=True)
        state["selected_articles"] = []
    finally:
        db.close()

    return state


def curate_contrarian_node(state: DigestState) -> DigestState:
    """
    Node 4: CurateContrarianNode (Conditional execution)
    Executed when echo_chamber_detected is True.
    Retrieves 1-2 articles offering opposing ideological perspectives.
    """
    if not state.get("echo_chamber_detected", False):
        state["contrarian_articles"] = []
        return state

    dominant_bias = state.get("dominant_bias", "Center")
    user_id_str = state.get("user_id")

    db = SessionLocal()
    try:
        user_uuid = uuid.UUID(user_id_str)
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()

        # Set target bias filter
        if dominant_bias == "Left":
            bias_filter = ArticleMetadata.bias_score > 0.2
        elif dominant_bias == "Right":
            bias_filter = ArticleMetadata.bias_score < -0.1
        else:
            bias_filter = (ArticleMetadata.bias_score > 0.3) | (ArticleMetadata.bias_score < -0.3)

        if profile and profile.interest_embedding is not None:
            user_embedding = profile.interest_embedding
            similarity = Article.article_embedding.cosine_distance(user_embedding).label("distance")

            query = (
                select(Article, ArticleMetadata, similarity)
                .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
                .where(Article.article_embedding.isnot(None))
                .where(bias_filter)
                .order_by(similarity, ArticleMetadata.source_credibility.desc())
                .limit(5)
            )
        else:
            query = (
                select(Article, ArticleMetadata)
                .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
                .where(bias_filter)
                .order_by(ArticleMetadata.source_credibility.desc())
                .limit(5)
            )

        results = db.execute(query).all()

        contrarians: List[Dict[str, Any]] = []
        for row in results:
            if len(row) == 3:
                article, metadata, distance = row
                match_pct = round((1 - float(distance)) * 100, 1) if distance is not None else 80.0
            else:
                article, metadata = row
                match_pct = 80.0

            bias_val = metadata.bias_score or 0.0
            if bias_val < -0.3:
                bias_label = "Left"
            elif bias_val > 0.3:
                bias_label = "Right"
            else:
                bias_label = "Center"

            content_summary = (article.content[:200] + "...") if article.content and len(article.content) > 200 else (article.content or article.title)

            contrarians.append({
                "article_id": str(article.id),
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "content_summary": content_summary,
                "match_percentage": match_pct,
                "bias": bias_label,
                "bias_score": bias_val,
                "credibility": metadata.source_credibility or 0.85,
                "topic": metadata.topic or "Perspective Check",
            })

            if len(contrarians) >= 2:
                break

        state["contrarian_articles"] = contrarians
        logger.info(f"[CurateContrarianNode] Curated {len(contrarians)} contrarian articles for user {user_id_str}")

    except Exception as e:
        logger.error(f"[CurateContrarianNode] Error fetching contrarian articles: {e}", exc_info=True)
        state["contrarian_articles"] = []
    finally:
        db.close()

    return state



def synthesize_digest_node(state: DigestState) -> DigestState:
    """
    Node 5: SynthesizeDigestNode
    Calls Groq LLM to synthesize a clean, responsive HTML email digest from the curated state.
    Includes Top Curated Stories, Perspective Check (if echo chamber detected), and Reading Insights.
    """
    selected = state.get("selected_articles", [])
    contrarians = state.get("contrarian_articles", [])
    risk = state.get("echo_chamber_risk", 0.0)
    detected = state.get("echo_chamber_detected", False)
    dominant_bias = state.get("dominant_bias", "Balanced")
    user_id = state.get("user_id", "Reader")

    # Simple fallback HTML generator in case Groq call is offline/unreachable
    def build_fallback_html() -> str:
        selected_items_html = "".join([
            f"""<div style="margin-bottom: 16px; padding: 12px; border-left: 3px solid #111; background-color: #f9f9f9;">
                <h4 style="margin: 0 0 6px 0;"><a href="{a['url']}" style="color: #111; text-decoration: none;">{a['title']}</a></h4>
                <p style="margin: 0; font-size: 12px; color: #555;"><strong>Source:</strong> {a['source']} | <strong>Bias:</strong> {a['bias']} | <strong>Match:</strong> {a['match_percentage']}%</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #333;">{a['content_summary']}</p>
            </div>""" for a in selected
        ])

        contrarian_items_html = ""
        if detected and contrarians:
            contrarian_items_html = "<h3 style='color: #c53030; margin-top: 24px;'>⚡ Perspective Check (Opposing Viewpoints)</h3>"
            contrarian_items_html += "".join([
                f"""<div style="margin-bottom: 16px; padding: 12px; border-left: 3px solid #c53030; background-color: #fff5f5;">
                    <h4 style="margin: 0 0 6px 0;"><a href="{a['url']}" style="color: #9b2c2c; text-decoration: none;">{a['title']}</a></h4>
                    <p style="margin: 0; font-size: 12px; color: #742a2a;"><strong>Source:</strong> {a['source']} | <strong>Bias:</strong> {a['bias']} Viewpoint</p>
                    <p style="margin: 6px 0 0 0; font-size: 13px; color: #2d3748;">{a['content_summary']}</p>
                </div>""" for a in contrarians
            ])

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Your AmpliNews Daily Digest</title></head>
        <body style="font-family: Georgia, serif; line-height: 1.6; color: #111; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-bottom: 2px solid #111; padding-bottom: 12px; margin-bottom: 20px; text-align: center;">
                <h1 style="font-size: 28px; margin: 0;">ampli<span style="color: #e53e3e;">.</span>news</h1>
                <p style="font-family: monospace; font-size: 11px; text-transform: uppercase; color: #666; margin-top: 4px;">Personalized AI News Digest & Perspective Agent</p>
            </div>
            <div style="margin-bottom: 20px;">
                <h2>Today's Top Curated Stories</h2>
                {selected_items_html}
            </div>
            {contrarian_items_html}
            <div style="border-top: 1px solid #ddd; margin-top: 30px; padding-top: 16px; font-family: monospace; font-size: 12px; color: #666;">
                <p><strong>Media Diet Insight:</strong> Echo Chamber Risk: {int(risk * 100)}% | Dominant Leaning: {dominant_bias}</p>
            </div>
        </body>
        </html>
        """

    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.GROQ_API_KEY)

        prompt_context = f"""
        User ID: {user_id}
        Echo Chamber Risk: {risk} (Detected: {detected})
        Dominant Reading Bias: {dominant_bias}
        
        Selected Personalized Articles:
        {selected}
        
        Contrarian Perspective Articles:
        {contrarians}
        """

        sys_prompt = """You are AmpliNews Agent, an AI news editor. Write a clean, responsive HTML email for the user's daily digest.
        Requirements:
        1. Professional newspaper editorial design inline CSS (Georgia serif font, clean borders).
        2. Header: ampli.news Daily Edition.
        3. Top Curated Stories section featuring the selected articles with title links, source, bias tag, and short summary.
        4. If echo_chamber_detected is True, add a prominent "Perspective Check ⚡" callout section introducing the contrarian articles with a friendly agent note encouraging media diet diversity.
        5. Reading Insights footer showing the user's Echo Chamber Risk rating.
        Return ONLY valid raw HTML code without markdown code blocks."""

        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt_context}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        html_content = response.choices[0].message.content.strip()
        # Clean up any potential markdown code fence markers
        if html_content.startswith("```"):
            html_content = html_content.split("```")[1]
            if html_content.startswith("html"):
                html_content = html_content[4:]
            html_content = html_content.strip()

        state["final_email_html"] = html_content
        state["status"] = "success"
        logger.info(f"[SynthesizeDigestNode] Successfully generated LLM HTML digest for user {user_id}")

    except Exception as e:
        logger.warning(f"[SynthesizeDigestNode] Groq synthesis failed, using fallback HTML generator: {e}")
        state["final_email_html"] = build_fallback_html()
        state["status"] = "success"

    return state




