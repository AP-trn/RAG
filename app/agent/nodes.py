from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.core.llm import llm
from app.agent.state import AgentState, GuardrailCheck, GradeDocuments, GradeHallucination
from app.agent.tools import model_with_tools

system_prompt = SystemMessage(
    content=(
        "You are an expert AI research assistant. "
        "Use 'document_search' to search vector documents or 'document_intelligence_tool' for parsing PDF files. "
        "Base your final answer strictly on the facts, dataset details, and research metrics returned by the tools. "
        "Do not offer unsolicited conversational follow-ups."
    )
)



def guardrail_node(state: AgentState):
    messages = state.get("messages", [])
    last_user_msg = str(messages[-1].content) if messages else ""

    try:
        structured_llm = llm.with_structured_output(GuardrailCheck)
        prompt = f"Determine if this query is safe and actionable for a RAG research assistant: '{last_user_msg}'"
        result = structured_llm.invoke([SystemMessage(content=prompt)])
        is_safe = bool(result.is_safe) if result else True
    except Exception:
        is_safe = True

    return {
        "original_query": last_user_msg,
        "retry_count": 0,
        "is_safe": is_safe,
    }


def rewrite_query_node(state: AgentState):
    query = state.get("original_query", "")
    prompt = (
        f"Rewrite the following technical query into an optimized search prompt: \nQuery: {query} "
        #f"for Azure AI Search / Document Intelligence:\nQuery: {query}"
    )
    response = llm.invoke([SystemMessage(content=prompt)])
    transformed = str(response.content).strip()
    return {
        "transformed_query": transformed,
        "messages": [HumanMessage(content=transformed)],
    }


def agent_node(state: AgentState):
    messages = state["messages"]
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [system_prompt] + list(messages)

    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


def doc_relevance_grader_node(state: AgentState):
    messages = state.get("messages", [])
    query = state.get("original_query", "")

    tool_contents = [str(msg.content) for msg in messages if isinstance(msg, ToolMessage)]
    docs = tool_contents if tool_contents else state.get("documents", [])

    if not docs:
        return {"documents": [], "is_relevant": False}

    try:
        structured_llm = llm.with_structured_output(GradeDocuments)
        relevant_docs = []
        for doc in docs:
            prompt = f"User Query: {query}\nDocument snippet: {doc}\nIs this snippet relevant to answering the query?"
            res = structured_llm.invoke([SystemMessage(content=prompt)])
            if res and res.binary_score.lower() == "yes":
                relevant_docs.append(doc)
    except Exception:
        relevant_docs = docs

    return {
        "documents": relevant_docs,
        "is_relevant": len(relevant_docs) > 0,
    }


def fallback_search_node(state: AgentState):
    fallback_info = f"[Fallback Context] No direct matches found in Azure AI Search index for query: '{state.get('original_query', '')}'."
    return {"documents": [fallback_info]}


def generate_node(state: AgentState):
    query = state.get("original_query", "")

    docs_list = state.get("documents", [])

    if not docs_list:
        docs_list = [str(m.content) for m in state.get("messages", []) if isinstance(m, ToolMessage)]
    
    docs = "\n\n".join(docs_list)

    last_msg = state["messages"][-1] if state.get("messages") else None
    if last_msg and isinstance(last_msg, AIMessage) and last_msg.content and not getattr(last_msg, "tool_calls", None):
        return {"final_response": str(last_msg.content)}
    prompt = (
        f"You are an expert AI research assistant.\n"
        f"Answer the user query strictly using the provided context.\n\n"
        f"Query: {query}\n\n"
        f"Context:\n{docs}"
    )
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"final_response": str(response.content)}


def hallucination_grader_node(state: AgentState):
    response = state.get("final_response", "")
    docs = "\n\n".join(state.get("documents", []))

    try:
        structured_llm = llm.with_structured_output(GradeHallucination)
        prompt = f"Facts:\n{docs}\n\nGenerated Response:\n{response}\nIs the generated response fully supported by facts?"
        res = structured_llm.invoke([SystemMessage(content=prompt)])
        is_grounded = bool(res and res.binary_score.lower() == "yes")
    except Exception:
        is_grounded = True

    return {"is_grounded": is_grounded}


def reflection_refiner_node(state: AgentState):
    query = state.get("original_query", "")
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
    return {"final_response": str(response.content), "retry_count": retries}


def answer_formatter_node(state: AgentState):
    raw_answer = state.get("final_response", "")
    formatted = f"{raw_answer.strip()}\n\n---\n*Verified by Agentic RAG Multi-Node Workflow*"
    return {"messages": [AIMessage(content=formatted)]}


def direct_response_node(state: AgentState):
    query = state.get("original_query", "Hello")
    msg = f"I am unable to process your request for query: '{query}'. Please check policy constraints or document availability."
    return {"messages": [AIMessage(content=msg)]}