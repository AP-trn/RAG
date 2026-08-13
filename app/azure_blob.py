import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

blob_service = BlobServiceClient.from_connection_string(connection_string)
container = blob_service.get_container_client(container_name)

def upload_pdf_to_blob(file_bytes: bytes, filename: str) -> str:
    blob_client = container.get_blob_client(filename)
    blob_client.upload_blob(file_bytes, overwrite=True)
    return blob_client.url