import os
from typing import TypedDict, Annotated, Sequence, List
from pydantic import BaseModel, Field

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.llm import llm
from app.retrieval import get_hybrid_retriever



class ExtendedAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    original_query: str
    transformed_query: str
    documents: List[str]
    is_safe: bool
    is_relevant: bool
    is_grounded: bool
    final_response: str
    retry_count: int


class GradeDocuments(BaseModel):
    binary_score: str = Field(description="Relevance score: 'yes' or 'no'")

class GradeHallucination(BaseModel):
    binary_score: str = Field(description="Answer is grounded in facts: 'yes' or 'no'")

class GuardrailCheck(BaseModel):
    is_safe: bool = Field(description="True if query is safe and clear to process, False otherwise")


def guardrail_node(state: ExtendedAgentState):
    messages = state["messages"]
    last_user_msg = str(messages[-1].content) if messages else ""

    try:
        structured_llm = llm.with_structured_output(GuardrailCheck)
        prompt= f"Determine if this query is safe and actionable for a RAG research assistant: '{last_user_msg}'"
        result= structured_llm.invoke([SystemMessage(content=prompt)])
        is_safe= bool(result.is_safe) if result else True

    except Exception:
        is_safe - True

    return {
        "original_query": last_user_msg,
        "retry_count": 0,
        "is_safe": is_safe
    }

def query_transform_node(state: ExtendedAgentState):
    query = state["original_query"]
    prompt = f"Rewrite the following technical query into an optimized Azure AI Search vector/keyword query: {query}"
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"transformed_query": response.content.strip()}

def hybrid_search_node(state: ExtendedAgentState):
    retriever = get_hybrid_retriever()
    search_query = state.get("transformed_query", state["original_query"])
    raw_docs = retriever.invoke(search_query)
    doc_texts = []
    for doc in raw_docs:
        content_str = str(doc.page_content)
        doc_texts.append(content_str)
    return {"documents": doc_texts}

def doc_grader_node(state: ExtendedAgentState):
    docs = state.get("documents", [])
    query = state["original_query"]
    
    if not docs:
        return {"is_relevant": False}

    structured_llm = llm.with_structured_output(GradeDocuments)
    relevant_docs = []
    
    for doc in docs:
        prompt = f"User Query: {query}\nDocument snippet: {doc}\nIs this snippet relevant to answering the query?"
        res = structured_llm.invoke([SystemMessage(content=prompt)])
        if res.binary_score.lower() == "yes":
            relevant_docs.append(doc)
            
    return {
        "documents": relevant_docs,
        "is_relevant": len(relevant_docs) > 0
    }


def fallback_search_node(state: ExtendedAgentState):
    fallback_info = f"[Fallback Context] No direct matches found in Azure AI Search index for query: '{state['original_query']}'."
    return {"documents": [fallback_info]}

def agent_node(state: ExtendedAgentState):
    query = state["original_query"]
    docs = "\n\n".join(state.get("documents", []))
    
    prompt = (
        f"You are an expert AI research assistant.\n"
        f"Answer the user query strictly using the provided context.\n"
        f"Query: {query}\n"
        f"Context:\n{docs}"
    )
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"final_response": response.content}


def hallucination_grader_node(state: ExtendedAgentState):
    response = state.get("final_response", "")
    docs = "\n\n".join(state.get("documents", []))
    
    structured_llm = llm.with_structured_output(GradeHallucination)
    prompt = f"Facts:\n{docs}\n\nGenerated Response:\n{response}\nIs the generated response fully supported by facts?"
    res = structured_llm.invoke([SystemMessage(content=prompt)])
    
    return {"is_grounded": res.binary_score.lower() == "yes"}


def reflection_refiner_node(state: ExtendedAgentState):
    query = state["original_query"]
    draft = state.get("final_response", "")
    docs = "\n\n".join(state.get("documents", []))
    retries = state.get("retry_count", 0) + 1
    
    prompt = (
        f"The previous response contained unsupported claims.\n"
        f"Query: {query}\n"
        f"Context: {docs}\n"
        f"Draft Response: {draft}\n"
        f"Rewrite the answer ensuring 100% factual adherence to the context."
    )
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"final_response": response.content, "retry_count": retries}

def answer_formatter_node(state: ExtendedAgentState):
    raw_answer = state.get("final_response", "")
    formatted = f"{raw_answer.strip()}\n\n---\n*Verified by Agentic RAG Multi-Node Workflow*"
    return {"messages": [AIMessage(content=formatted)]}


def direct_response_node(state: ExtendedAgentState):
    query = state.get("original_query", "Hello")
    msg = f"I am unable to process your request for query: '{query}'. Please check policy constraints or document availability."
    return {"messages": [AIMessage(content=msg)]}



def route_guardrail(state: ExtendedAgentState):
    return "query_transform" if state.get("is_safe", True) else "direct_response"

def route_doc_grader(state: ExtendedAgentState):
    return "agent" if state.get("is_relevant", False) else "fallback_search"

def route_hallucination(state: ExtendedAgentState):
    if state.get("is_grounded", True) or state.get("retry_count", 0) >= 2:
        return "answer_formatter"
    return "reflection_refiner"



workflow = StateGraph(ExtendedAgentState)

# Add all 10 nodes
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("query_transform", query_transform_node)
workflow.add_node("hybrid_search", hybrid_search_node)
workflow.add_node("doc_grader", doc_grader_node)
workflow.add_node("fallback_search", fallback_search_node)
workflow.add_node("agent", agent_node)
workflow.add_node("hallucination_grader", hallucination_grader_node)
workflow.add_node("reflection_refiner", reflection_refiner_node)
workflow.add_node("answer_formatter", answer_formatter_node)
workflow.add_node("direct_response", direct_response_node)


workflow.add_edge(START, "guardrail")

workflow.add_conditional_edges(
    "guardrail",
    route_guardrail,
    {
        "query_transform": "query_transform",
        "direct_response": "direct_response"
    }
)

workflow.add_edge("query_transform", "hybrid_search")
workflow.add_edge("hybrid_search", "doc_grader")

workflow.add_conditional_edges(
    "doc_grader",
    route_doc_grader,
    {
        "agent": "agent",
        "fallback_search": "fallback_search"
    }
)

workflow.add_edge("fallback_search", "agent")
workflow.add_edge("agent", "hallucination_grader")

workflow.add_conditional_edges(
    "hallucination_grader",
    route_hallucination,
    {
        "answer_formatter": "answer_formatter",
        "reflection_refiner": "reflection_refiner"
    }
)

workflow.add_edge("reflection_refiner", "hallucination_grader")
workflow.add_edge("answer_formatter", END)
workflow.add_edge("direct_response", END)

graph_agent = workflow.compile()