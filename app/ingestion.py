import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.azure_blob import upload_pdf_to_blob

router = APIRouter()

@router.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        content = await file.read()
        blob_url = upload_pdf_to_blob(content, file.filename)

        return {
            "status": "Success",
            "filename": file.filename,
            "blob_url": blob_url,
            "message": "File uploaded to Blob Storage. Azure AI Search Indexer will process it automatically."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store PDF in Azure Blob: {str(e)}")