# app/retrieval.py
import os
from dotenv import load_dotenv
from app.core.config import settings
from langchain_community.vectorstores.azuresearch import AzureSearch
from app.core.embedding import embeddings

vector_store = AzureSearch(
        azure_search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
        azure_search_key=settings.AZURE_SEARCH_KEY,
        index_name=settings.AZURE_SEARCH_INDEX_NAME,
        embedding_function=embeddings.embed_query,
        search_type="hybrid",
    )

def get_hybrid_retriever():
    return vector_store.as_retriever(
        search_type="hybrid",
        k=3
    )