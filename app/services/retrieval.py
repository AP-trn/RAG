# app/retrieval.py
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["AZURESEARCH_FIELDS_ID"] = "chunk_id"
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "chunk"
os.environ["AZURESEARCH_FIELDS_CONTENT_VECTOR"] = "text_vector"


from langchain_community.vectorstores.azuresearch import AzureSearch
from app.core.embedding import embeddings

vector_store = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    embedding_function=embeddings.embed_query,
    vector_field_name="text_vector",
    content_key="chunk"
)

def get_hybrid_retriever():
    return vector_store.as_retriever(
        search_type="hybrid",
        k=3
    )