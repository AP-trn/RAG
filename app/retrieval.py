import os
from dotenv import load_dotenv
from langchain_azure_ai.vectorstores import AzureSearch
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from embedding import embeddings
from llm import llm

load_dotenv()

# Initialize Azure AI Search Vector Store
azure_search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
azure_search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "rag-docs-index")

vector_store = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    embedding_function=embeddings.embed_query,
)

def get_hybrid_retriever():
    #Hybrid Search (Dense Vector + BM25 Full-Text)
    return vector_store.as_retriever(
        search_type="hybrid",
        k=3
    )

def get_multi_query_retriever():
    #Generates multiple query variations using LLM
    base_retriever = vector_store.as_retriever(
        search_type="hybrid",
        k=4
    )
    
    return MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm
    )