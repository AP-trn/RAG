from typing import TypedDict, Annotated, Sequence, List
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    original_query: str
    transformed_query: str
    documents: List[str]
    is_safe: bool
    is_relevant: bool
    is_grounded: bool
    final_response: str
    retry_count: int


class GuardrailCheck(BaseModel):
    is_safe: bool = Field(description="True if query is safe and actionable, False otherwise")


class GradeDocuments(BaseModel):
    binary_score: str = Field(description="Relevance score: 'yes' or 'no'")


class GradeHallucination(BaseModel):
    binary_score: str = Field(description="Answer is grounded in facts: 'yes' or 'no'")