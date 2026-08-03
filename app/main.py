from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from app.agent_graph import graph_agent
from app.ingestion import router as ingest_router

app = FastAPI(
    title="Advanced Azure Agentic RAG API",
    description="Agentic RAG using FastAPI, LangGraph, and Azure OpenAI",
    version="1.0.0"
)

# Include the ingestion router
app.include_router(ingest_router)

# Input Request Schema
class QueryRequest(BaseModel):
    question: str = Field(..., example="What is a brain tumor and how are deep learning models used to detect it?")

# Output Response Schema
class QueryResponse(BaseModel):
    response: str

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        # Initialize inputs with user message
        inputs = {"messages": [HumanMessage(content=request.question)]}
        
        # Invoke LangGraph ReAct agent asynchronously
        result = await graph_agent.ainvoke(inputs)
        
        # Extract the final answer from the last message node
        final_message = result["messages"][-1]
        final_answer = final_message.content
        
        # Ensure answer is string-formatted if LLM returns complex content blocks
        if isinstance(final_answer, list):
            final_answer = "\n".join([str(block) for block in final_answer])

        return QueryResponse(response=final_answer.strip())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")