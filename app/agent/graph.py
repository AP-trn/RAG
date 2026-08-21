from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.agent.tools import tools
from app.agent.nodes import (
    guardrail_node,
    rewrite_query_node,
    agent_node,
    doc_relevance_grader_node,
    fallback_search_node,
    generate_node,
    hallucination_grader_node,
    reflection_refiner_node,
    answer_formatter_node,
    direct_response_node,
)
from app.agent.edges import (
    route_guardrail,
    route_agent_action,
    route_doc_relevance_grader,
    route_hallucination,
)

retrieve= ToolNode(tools)

workflow = StateGraph(AgentState)


workflow.add_node("guardrail", guardrail_node)
workflow.add_node("rewrite", rewrite_query_node)
workflow.add_node("agent", agent_node)
workflow.add_node("retrieve", retrieve)
workflow.add_node("doc_grader", doc_relevance_grader_node)
workflow.add_node("fallback_search", fallback_search_node)
workflow.add_node("generate", generate_node)
workflow.add_node("hallucination_grader", hallucination_grader_node)
workflow.add_node("reflection_refiner", reflection_refiner_node)
workflow.add_node("answer_formatter", answer_formatter_node)
workflow.add_node("direct_response", direct_response_node)


workflow.add_edge(START, "guardrail")

workflow.add_conditional_edges(
    "guardrail",
    route_guardrail,
    {
        "rewrite": "rewrite",
        "direct_response": "direct_response",
    },
)

workflow.add_edge("rewrite", "agent")

workflow.add_conditional_edges(
    "agent",
    route_agent_action,
    {
        "retrieve": "retrieve",
        "doc_grader": "doc_grader",
    },
)


workflow.add_edge("retrieve", "agent")


workflow.add_conditional_edges(
    "doc_grader",
    route_doc_relevance_grader,
    {
        "generate": "generate",
        "fallback_search": "fallback_search",
    },
)
workflow.add_edge("fallback_search", "generate")


workflow.add_edge("generate", "hallucination_grader")

workflow.add_conditional_edges(
    "hallucination_grader",
    route_hallucination,
    {
        "answer_formatter": "answer_formatter",
        "reflection_refiner": "reflection_refiner",
    },
)

workflow.add_edge("reflection_refiner", "hallucination_grader")
workflow.add_edge("answer_formatter", END)
workflow.add_edge("direct_response", END)

graph_agent = workflow.compile()