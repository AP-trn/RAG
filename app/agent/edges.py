from typing import Literal
from app.agent.state import AgentState

def route_guardrail(state: AgentState) -> Literal["rewrite", "direct_response"]:
    return "rewrite" if state.get("is_safe", True) else "direct_response"


def route_agent_action(state: AgentState) -> Literal["retrieve", "doc_grader"]:
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None
    if last_msg and getattr(last_msg, "tool_calls", None):
        return "retrieve"
    return "doc_grader"


def route_doc_relevance_grader(state: AgentState) -> Literal["generate", "fallback_search"]:
    return "generate" if state.get("is_relevant", False) else "fallback_search"


def route_hallucination(state: AgentState) -> Literal["answer_formatter", "reflection_refiner"]:
    if state.get("is_grounded", True) or state.get("retry_count", 0) >= 2:
        return "answer_formatter"
    return "reflection_refiner"
