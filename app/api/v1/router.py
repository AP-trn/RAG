from fastapi import APIRouter
from app.api.v1.ingestion import router as ingest_router
from app.api.v1.agent import router as agent_router
from app.api.v1.evaluation import router as eval_router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(ingest_router)
api_v1_router.include_router(agent_router)

api_v1_router.include_router(eval_router)