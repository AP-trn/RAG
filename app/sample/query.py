from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        example="What is a brain tumor and how are deep learning models used to detect it?",
    )


class QueryResponse(BaseModel):
    response: str