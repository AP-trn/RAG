import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv()


raw_embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
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