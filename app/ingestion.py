import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf_loader import extract_text_from_pdf
from chunking import recursive_chunking, semantic_chunking
from retrieval import vector_store
from embedding import embeddings  # Added embeddings import for semantic chunking

router = APIRouter()
UPLOAD_DIR = Path("data/pdfs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def process_and_store_pdf(pdf_path: Path, filename: str, strategy: str = "recursive"):
    """Extracts text, chunks it based on strategy, and uploads to Azure AI Search."""
    text = extract_text_from_pdf(str(pdf_path))
    
    if not text.strip():
        raise ValueError(f"No extractable text found in file {filename}.")

    # 1. Choose chunking strategy
    if strategy == "semantic":
        # FIX: Added required 'embeddings' argument
        chunks, chunk_ids = semantic_chunking(text, filename, embeddings)
    else:
        chunks, chunk_ids = recursive_chunking(text, filename)

    # 2. Upload directly to Azure AI Search in batches
    batch_size = 200
    for i in range(0, len(chunks), batch_size):
        vector_store.add_documents(
            documents=chunks[i : i + batch_size],
            ids=chunk_ids[i : i + batch_size]
        )


@router.post("/ingest")
async def ingest_pdf(
    file: UploadFile = File(...), 
    strategy: str = "recursive"
):
    """API Endpoint to upload and ingest a PDF document into Azure AI Search."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_path = UPLOAD_DIR / file.filename

    try:
        content = await file.read()
        with open(pdf_path, "wb") as buffer:
            buffer.write(content)

        process_and_store_pdf(pdf_path, file.filename, strategy)

        return {
            "status": "Success",
            "filename": file.filename,
            "strategy": strategy,
            "message": "Successfully indexed in Azure AI Search."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")