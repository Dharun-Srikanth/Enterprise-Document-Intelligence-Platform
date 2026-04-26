"""Query API routes (structured + analytical)."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.database import get_db

router = APIRouter(prefix="/api/query", tags=["query"])
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str


class StructuredQueryResponse(BaseModel):
    question: str
    sql: str | None = None
    results: list[dict] | None = None
    assumptions: list[str] | None = None
    error: str | None = None


class AnalyticalQueryResponse(BaseModel):
    question: str
    answer: str | None = None
    sources: list[dict] | None = None
    confidence: float | None = None
    error: str | None = None


@router.post("/structured", response_model=StructuredQueryResponse)
async def structured_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Natural language → SQL query agent."""
    try:
        from app.services.sql_agent.orchestrator import run_structured_query

        result = await run_structured_query(request.question, db=db)

        return StructuredQueryResponse(
            question=result.question,
            sql=result.sql,
            results=result.results,
            assumptions=result.assumptions,
            error=result.error,
        )
    except Exception as e:
        logger.exception(f"Structured query failed: {e}")
        return StructuredQueryResponse(
            question=request.question,
            error=f"Query processing failed: {str(e)}",
        )


@router.post("/analytical", response_model=AnalyticalQueryResponse)
async def analytical_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """RAG-based analytical query with multi-hop retrieval."""
    try:
        from app.services.rag.orchestrator import run_analytical_query

        result = await run_analytical_query(request.question, db=db)

        return AnalyticalQueryResponse(
            question=result.question,
            answer=result.answer,
            sources=result.sources,
            confidence=result.confidence,
            error=result.error,
        )
    except Exception as e:
        logger.exception(f"Analytical query failed: {e}")
        return AnalyticalQueryResponse(
            question=request.question,
            error=f"Query processing failed: {str(e)}",
        )
