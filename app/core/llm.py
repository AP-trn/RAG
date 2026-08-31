from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from app.core.config import settings


llm = AzureChatOpenAI(
    azure_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
    openai_api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    temperature=0,
)