import traceback
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


app.include_router(ingest_router)

class QueryRequest(BaseModel):
    question: str = Field(..., example="What is a brain tumor and how are deep learning models used to detect it?")


class QueryResponse(BaseModel):
    response: str

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        inputs = {"messages": [HumanMessage(content=request.question)]}
        
        result = await graph_agent.ainvoke(inputs)
        
        final_message = result["messages"][-1]
        final_answer = final_message.content
        
        if isinstance(final_answer, list):
            final_answer = "\n".join([str(block) for block in final_answer])

        return QueryResponse(response=str(final_answer).strip())

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")