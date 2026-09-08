"""
FastAPI Main Application Entrypoint for Fact Knowledge Layer.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.db.database import init_db
from app.db.repositories import DocumentRepository, FactRepository, ComparisonRepository
from app.api.routes_documents import router as doc_router
from app.api.routes_facts import router as fact_router
from app.api.routes_comparison import router as comp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database schema
    logger.info("Starting up Fact Knowledge Layer API...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down Fact Knowledge Layer API...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Fact Knowledge Layer: Multi-document evidence-grounded fact extraction & cross-document reconciliation system.",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(doc_router)
app.include_router(fact_router)
app.include_router(comp_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint returning system diagnostics and database statistics."""
    doc_count = len(DocumentRepository.list_documents())
    fact_count = FactRepository.count_facts()
    comp_summary = ComparisonRepository.get_summary()

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "database_url": settings.database_url,
        "statistics": {
            "documents_count": doc_count,
            "facts_count": fact_count,
            "comparisons_total": comp_summary.total_comparisons,
            "corroborated": comp_summary.corroborated_count,
            "contradiction": comp_summary.contradiction_count,
            "contextual": comp_summary.contextual_count,
            "unknown": comp_summary.unknown_count
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
