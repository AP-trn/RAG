from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import create_retriever_tool
from app.llm import llm
from app.retrieval import get_hybrid_retriever

# State Definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Retriever Tool Configuration
retriever_tool = create_retriever_tool(
    get_hybrid_retriever(),
    name="document_search",
    description="Mandatory tool. Search the vector store to extract technical, medical, and analytical facts from uploaded documents."
)
tools = [retriever_tool]

# Model Binding
model_with_tools = llm.bind_tools(tools)

# Strict System Instruction
SYSTEM_INSTRUCTION = SystemMessage(
    content=(
        "You are an expert AI research assistant. "
        "Always search the knowledge base using the 'document_search' tool before answering questions. "
        "Base your final answer strictly on the facts, dataset details, and research metrics returned by the tool. "
        "Do not offer unsolicited conversational follow-ups (such as 'If you want, I can also explain...')."
    )
)

# Graph Nodes
def agent_node(state: AgentState):
    messages = state["messages"]
    
    # Prepend system instruction if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SYSTEM_INSTRUCTION] + list(messages)
        
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 6. Graph Assembly
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

graph_agent = workflow.compile()