"""
SQL Agent Orchestrator — coordinates NL→SQL generation, validation, execution.

Pipeline:
1. Generate SQL from natural language
2. Validate for safety (SELECT only, no injection)
3. Execute against PostgreSQL
4. If error → regenerate with error context → retry (max 2)
5. Log query for audit
"""

import uuid
import time
import logging
from dataclasses import dataclass

from app.services.sql_agent.generator import generate_sql, regenerate_sql
from app.services.sql_agent.validator import validate_sql
from app.services.sql_agent.executor import execute_sql

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


@dataclass
class StructuredResponse:
    question: str
    sql: str | None
    results: list[dict] | None
    assumptions: list[str] | None
    error: str | None = None


async def run_structured_query(
    question: str,
    db=None,
) -> StructuredResponse:
    """
    Full NL→SQL pipeline with error recovery.

    1. LLM generates SQL
    2. Validator checks safety
    3. Executor runs query
    4. On failure → regenerate with error feedback → retry
    """
    import asyncio
    start_time = time.time()

    if not question or not question.strip():
        return StructuredResponse(
            question=question,
            sql=None,
            results=None,
            assumptions=None,
            error="Question cannot be empty.",
        )

    if not db:
        return StructuredResponse(
            question=question,
            sql=None,
            results=None,
            assumptions=None,
            error="Database connection not available.",
        )

    # Step 1: Generate SQL
    gen_result = await asyncio.to_thread(generate_sql, question)

    if gen_result["error"] or not gen_result["sql"]:
        return StructuredResponse(
            question=question,
            sql=None,
            results=None,
            assumptions=gen_result.get("assumptions"),
            error=gen_result.get("error", "Failed to generate SQL"),
        )

    current_sql = gen_result["sql"]
    assumptions = gen_result.get("assumptions", [])
    last_error = None

    # Step 2-4: Validate → Execute → Retry loop
    for attempt in range(1 + MAX_RETRIES):
        # Validate
        validation = validate_sql(current_sql)

        if not validation["valid"]:
            error_msg = "; ".join(validation["errors"])
            logger.warning(f"SQL validation failed (attempt {attempt+1}): {error_msg}")

            if attempt < MAX_RETRIES:
                # Regenerate with error feedback
                retry_result = await asyncio.to_thread(
                    regenerate_sql, question, current_sql, error_msg
                )
                if retry_result["sql"]:
                    current_sql = retry_result["sql"]
                    if retry_result.get("assumptions"):
                        assumptions = retry_result["assumptions"]
                    continue

            return StructuredResponse(
                question=question,
                sql=current_sql,
                results=None,
                assumptions=assumptions,
                error=f"SQL validation failed: {error_msg}",
            )

        # Add validation warnings to assumptions
        if validation["warnings"]:
            assumptions.extend(validation["warnings"])

        # Execute
        exec_result = await execute_sql(db, current_sql)

        if exec_result["error"]:
            error_msg = exec_result["error"]
            logger.warning(f"SQL execution failed (attempt {attempt+1}): {error_msg}")
            last_error = error_msg

            if attempt < MAX_RETRIES:
                # Regenerate with execution error
                retry_result = await asyncio.to_thread(
                    regenerate_sql, question, current_sql, error_msg
                )
                if retry_result["sql"]:
                    current_sql = retry_result["sql"]
                    if retry_result.get("assumptions"):
                        assumptions = retry_result["assumptions"]
                    continue

            return StructuredResponse(
                question=question,
                sql=current_sql,
                results=None,
                assumptions=assumptions,
                error=f"SQL execution failed: {error_msg}",
            )

        # Success!
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Log query
        if db:
            try:
                await _log_query(
                    db=db,
                    query_type="structured",
                    user_query=question,
                    generated_sql=current_sql,
                    confidence=1.0 if not exec_result.get("truncated") else 0.9,
                    execution_time_ms=elapsed_ms,
                )
            except Exception as e:
                logger.warning(f"Query logging failed: {e}")

        return StructuredResponse(
            question=question,
            sql=current_sql,
            results=exec_result["results"],
            assumptions=assumptions,
        )

    # Should not reach here, but just in case
    return StructuredResponse(
        question=question,
        sql=current_sql,
        results=None,
        assumptions=assumptions,
        error=f"Query failed after {MAX_RETRIES + 1} attempts: {last_error}",
    )


async def _log_query(
    db,
    query_type: str,
    user_query: str,
    generated_sql: str | None = None,
    confidence: float | None = None,
    execution_time_ms: int | None = None,
):
    """Store query log in database for audit trail."""
    from app.models.query_log import QueryLog

    log = QueryLog(
        id=uuid.uuid4(),
        query_type=query_type,
        user_query=user_query,
        generated_sql=generated_sql,
        confidence=confidence,
        execution_time_ms=execution_time_ms,
    )
    db.add(log)
    await db.commit()
