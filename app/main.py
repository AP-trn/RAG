import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": "Health",
        "description": "API status and uptime checks.",
    },
    {
        "name": "Ingestion",
        "description": "Upload, parse, and index PDF documents into Azure AI Search.",
    },
    {
        "name": "Agent",
        "description": "Execute the 10-node Agentic RAG graph with multi-hop reasoning.",
    },
    {
        "name": "Evaluation",
        "description": "Evaluate pipeline metrics (Faithfulness, Relevancy, Recall) via Ragas.",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    yield
   
    logger.info("Application shutdown complete.")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.APP_ENV.lower() != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    
    @app.get("/health", tags=["Health"], summary="Service Health Check")
    async def health():
        return {"status": "ok", "environment": settings.APP_ENV}
    app.include_router(api_v1_router)
    
    return app


app = create_app()