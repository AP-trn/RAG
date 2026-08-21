import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from datasets import Dataset
from langchain_core.messages import HumanMessage
from ragas import evaluate
from ragas.metrics import (faithfulness, answer_relevancy, context_precision, context_recall)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from app.core.llm import llm, embeddings
from app.agent.graph import graph_agent


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/eval", tags=["Evaluation"])


eval_llm = LangchainLLMWrapper(llm)
eval_embeddings = LangchainEmbeddingsWrapper(embeddings)
target_metrics = [
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
]


class EvaluationRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=3)
    ground_truth: str = Field(..., min_length=3)


class EvaluationResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    ragas_scores: Dict[str, float]
    retrieved_contexts: List[str]


def extract_contexts(graph_state: dict) -> List[str]:
    """Pulls retrieved chunks from state or tool message trace."""
    docs = graph_state.get("documents", [])
    if docs:
        return docs

    tool_outputs = [
        str(m.content)
        for m in graph_state.get("messages", [])
        if getattr(m, "type", None) == "tool" or m.__class__.__name__ == "ToolMessage"
    ]
    return tool_outputs if tool_outputs else ["No context retrieved."]


def extract_answer(graph_state: dict) -> str:
    """Extracts the final response text from the last graph message."""
    messages = graph_state.get("messages", [])
    if not messages:
        return ""

    raw_content = messages[-1].content
    if isinstance(raw_content, list):
        return "\n".join(str(item) for item in raw_content).strip()
    return str(raw_content).strip()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_agentic_rag(request: EvaluationRequest):
    try:
        graph_output = await graph_agent.ainvoke(
            {"messages": [HumanMessage(content=request.question)], "retry_count": 0},
            config={"recursion_limit": 25},
        )

        final_answer = extract_answer(graph_output)
        contexts = extract_contexts(graph_output)

        eval_payload = {
            "question": [request.question],
            "user_input": [request.question],
            "answer": [final_answer],
            "response": [final_answer],
            "contexts": [contexts],
            "retrieved_contexts": [contexts],
            "ground_truth": [request.ground_truth],
            "reference": [request.ground_truth],
        }

        dataset= Dataset.from_dict(eval_payload)

        score_results = evaluate(
            dataset=dataset,
            metrics=target_metrics,
            llm=eval_llm,
            embeddings=eval_embeddings,
        )

        scores = {
            metric.name: round(float(score_results[metric.name]), 4)
            for metric in target_metrics
            if metric.name in score_results
        }

        return EvaluationResponse(
            session_id=request.session_id,
            question=request.question,
            answer=final_answer,
            ragas_scores=scores,
            retrieved_contexts=contexts,
        )

    except Exception as err:
        logger.error(f"Eval run failed for session {request.session_id}: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation pipeline failed: {str(err)}",
        )