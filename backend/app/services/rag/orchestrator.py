"""
RAG Orchestrator — coordinates Retriever → Synthesizer pipeline.

Handles:
- Full pipeline: decompose → search → synthesize → respond
- Fault tolerance: no results, partial, LLM failures
- Query logging for audit trail
"""

import uuid
import time
import logging
from dataclasses import dataclass, asdict

from app.services.rag.retriever_agent import retrieve, RetrievalResult
from app.services.rag.synthesizer_agent import synthesize, SynthesisResult

logger = logging.getLogger(__name__)


@dataclass
class AnalyticalResponse:
    question: str
    answer: str | None
    sources: list[dict] | None
    confidence: float | None
    error: str | None = None


async def run_analytical_query(
    question: str,
    db=None,
    top_k: int = 10,
) -> AnalyticalResponse:
    """
    Full RAG pipeline:
    1. Retriever Agent decomposes + searches
    2. Synthesizer Agent reasons + generates answer
    3. Log query for audit
    """
    import asyncio
    start_time = time.time()

    if not question or not question.strip():
        return AnalyticalResponse(
            question=question,
            answer=None,
            sources=None,
            confidence=None,
            error="Question cannot be empty.",
        )

    # Step 1: Retrieve
    try:
        retrieval: RetrievalResult = await asyncio.to_thread(retrieve, question, top_k)
    except Exception as e:
        logger.exception(f"Retrieval failed: {e}")
        return AnalyticalResponse(
            question=question,
            answer=None,
            sources=None,
            confidence=None,
            error=f"Document retrieval failed: {str(e)}",
        )

    if retrieval.error:
        return AnalyticalResponse(
            question=question,
            answer=None,
            sources=None,
            confidence=None,
            error=retrieval.error,
        )

    # Step 2: Synthesize
    try:
        synthesis: SynthesisResult = await asyncio.to_thread(
            synthesize, question, retrieval.chunks, retrieval.sub_queries
        )
    except Exception as e:
        logger.exception(f"Synthesis failed: {e}")
        return AnalyticalResponse(
            question=question,
            answer=None,
            sources=None,
            confidence=None,
            error=f"Answer synthesis failed: {str(e)}",
        )

    # Build source references for response
    sources = None
    if synthesis.sources:
        sources = [
            {
                "document_id": s.document_id,
                "filename": s.filename,
                "section": s.section,
                "preview": s.chunk_text_preview,
                "relevance_score": round(s.relevance_score, 3),
            }
            for s in synthesis.sources
        ]

    # Build answer text
    answer = synthesis.answer
    if synthesis.not_found:
        answer = (
            "Information not found in the ingested documents. "
            + (synthesis.reasoning_notes or "The query topic does not appear in the available corpus.")
        )
    elif synthesis.partial and synthesis.reasoning_notes:
        answer = f"{synthesis.answer}\n\n⚠️ Note: {synthesis.reasoning_notes}"

    # Step 3: Log query (async, non-blocking)
    elapsed_ms = int((time.time() - start_time) * 1000)
    if db:
        try:
            await _log_query(
                db=db,
                query_type="analytical",
                user_query=question,
                sources=sources,
                confidence=synthesis.confidence,
                error=synthesis.error,
                execution_time_ms=elapsed_ms,
            )
        except Exception as e:
            logger.warning(f"Query logging failed: {e}")

    return AnalyticalResponse(
        question=question,
        answer=answer,
        sources=sources,
        confidence=synthesis.confidence,
        error=synthesis.error,
    )


async def _log_query(
    db,
    query_type: str,
    user_query: str,
    sources: list[dict] | None = None,
    confidence: float | None = None,
    error: str | None = None,
    execution_time_ms: int | None = None,
    generated_sql: str | None = None,
):
    """Store query log in database for audit trail."""
    from app.models.query_log import QueryLog

    log = QueryLog(
        id=uuid.uuid4(),
        query_type=query_type,
        user_query=user_query,
        generated_sql=generated_sql,
        sources=sources,
        confidence=confidence,
        error=error,
        execution_time_ms=execution_time_ms,
    )
    db.add(log)
    await db.commit()
