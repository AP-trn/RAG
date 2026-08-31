import os
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from app.core.config import settings
from dotenv import load_dotenv


load_dotenv()


raw_embeddings = AzureOpenAIEmbeddings(
    azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    openai_api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
)

class PureFloatAzureEmbeddings:
    def __init__(self, base_embeddings):
        self._base = base_embeddings

    def embed_query(self, text: str) -> list[float]:
        vector = self._base.embed_query(text)
        return [float(x) for x in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self._base.embed_documents(texts)
        return [[float(x) for x in vec] for vec in vectors]

embeddings = PureFloatAzureEmbeddings(raw_embeddings)