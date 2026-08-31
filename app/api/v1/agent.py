import logging
from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage

from app.agent.graph import graph_agent
from app.core.config import settings
from app.sample.query import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Agentic RAG Pipeline",
)
async def query_agent(request: QueryRequest):
    try:
        inputs = {"messages": [HumanMessage(content=request.question)]}

       
        result = await graph_agent.ainvoke(
            inputs,
            config={"recursion_limit": settings.RECURSION_LIMIT},
        )

        final_message = result["messages"][-1]
        final_answer = final_message.content

        if isinstance(final_answer, list):
            final_answer = "\n".join(str(block) for block in final_answer)

        return QueryResponse(response=str(final_answer).strip())

    except Exception as exc:
        logger.exception("Agent execution failed for query: %s", request.question)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent Execution Error: {str(exc)}",
        ) from exc