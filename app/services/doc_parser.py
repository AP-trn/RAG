import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest, 
    DocumentContentFormat
)

from app.core.config import settings



di_client = DocumentIntelligenceClient(
    endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
    credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
)

def analyze_pdf_bytes(file_bytes: bytes) -> str:
    poller = di_client.begin_analyze_document(
        model_id="prebuilt-layout",
        analyze_request=AnalyzeDocumentRequest(bytes_source=file_bytes),
        output_content_format=DocumentContentFormat.MARKDOWN
    )
    result = poller.result()
    return result.content  