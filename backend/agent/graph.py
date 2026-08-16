"""Phase 9: LangGraph State Machine Workflow Assembly for AmpliNews."""
import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END

from agent.state import DigestState
from agent.nodes import (
    retrieve_context_node,
    analyze_bias_node,
    curate_standard_node,
    curate_contrarian_node,
    synthesize_digest_node,
)

logger = logging.getLogger(__name__)


def should_curate_contrarian(state: DigestState) -> Literal["curate_contrarian", "synthesize_digest"]:
    """
    Conditional Edge Router:
    Checks if an echo chamber bubble was detected. If True, routes to curate_contrarian.
    Otherwise, bypasses directly to synthesize_digest.
    """
    if state.get("echo_chamber_detected", False):
        logger.info(f"[GraphRouter] Echo chamber detected for user {state.get('user_id')}. Routing to curate_contrarian.")
        return "curate_contrarian"
    logger.info(f"[GraphRouter] No echo chamber bubble detected. Bypassing directly to synthesize_digest.")
    return "synthesize_digest"


def create_digest_workflow() -> StateGraph:
    """Builds and compiles the LangGraph StateMachine."""
    workflow = StateGraph(DigestState)

    # 1. Register Nodes
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("analyze_bias", analyze_bias_node)
    workflow.add_node("curate_standard", curate_standard_node)
    workflow.add_node("curate_contrarian", curate_contrarian_node)
    workflow.add_node("synthesize_digest", synthesize_digest_node)

    # 2. Define Linear Flow
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "analyze_bias")
    workflow.add_edge("analyze_bias", "curate_standard")

    # 3. Add Conditional Routing Edge
    workflow.add_conditional_edges(
        "curate_standard",
        should_curate_contrarian,
        {
            "curate_contrarian": "curate_contrarian",
            "synthesize_digest": "synthesize_digest",
        },
    )

    workflow.add_edge("curate_contrarian", "synthesize_digest")
    workflow.add_edge("synthesize_digest", END)

    return workflow.compile()


# Compiled LangGraph Application Instance
digest_agent_app = create_digest_workflow()


def run_digest_agent(user_id: str) -> DigestState:
    """
    Convenience wrapper to run the full LangGraph state machine for a user.
    """
    initial_state: DigestState = {
        "user_id": user_id,
        "user_email": None,
        "reading_history": [],
        "echo_chamber_risk": 0.0,
        "echo_chamber_detected": False,
        "dominant_bias": "Balanced",
        "top_topic": None,
        "selected_articles": [],
        "contrarian_articles": [],
        "final_email_html": "",
        "status": "pending",
        "error_message": None,
    }

    result = digest_agent_app.invoke(initial_state)
    return result
