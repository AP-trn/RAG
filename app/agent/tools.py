import os
from langchain_core.tools import create_retriever_tool, tool
from app.core.llm import llm
from app.services.retrieval import get_hybrid_retriever
from app.services.doc_parser import analyze_pdf_bytes

retriever_tool = create_retriever_tool(
    get_hybrid_retriever(),
    name="document_search",
    description="Search the vector store for technical, medical, and analytical facts from uploaded documents."
)

@tool(description="Extracts tables, layouts, and markdown text from PDF files using Azure Document Intelligence.")
def document_intelligence_tool(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"File '{file_path}' does not exist on disk."
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        markdown_content = analyze_pdf_bytes(file_bytes)
        return markdown_content[:8000]
    except Exception as exc:
        return f"Error analyzing PDF with Document Intelligence: {str(exc)}"

tools = [retriever_tool, document_intelligence_tool]
model_with_tools = llm.bind_tools(tools)