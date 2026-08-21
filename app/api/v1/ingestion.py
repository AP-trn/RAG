import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.azure_blob import upload_pdf_to_blob
from app.services.doc_parser import analyze_pdf_bytes

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post("", summary="Ingest PDF", status_code=status.HTTP_200_OK)
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        content = await file.read()

        markdown_text = analyze_pdf_bytes(content)
        
        blob_url = upload_pdf_to_blob(content, file.filename)

        return {
            "status": "Success",
            "filename": file.filename,
            "blob_url": blob_url,
            "message": "File uploaded to Blob Storage. Azure AI Search Indexer will process it automatically."
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to store PDF in Azure Blob: {str(e)}")