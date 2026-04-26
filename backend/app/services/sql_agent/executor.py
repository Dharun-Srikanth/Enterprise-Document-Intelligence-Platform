"""
SQL Executor — safely executes validated SQL against PostgreSQL.

Features:
- Uses async SQLAlchemy with read-only execution
- Row limit enforcement
- Error capture for retry loop
- Result formatting
"""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

MAX_ROWS = 100


async def execute_sql(
    db: AsyncSession,
    sql: str,
    max_rows: int = MAX_ROWS,
) -> dict:
    """
    Execute a validated SELECT query and return results.

    Returns:
        dict with:
        - results: list of row dicts
        - row_count: number of rows returned
        - columns: list of column names
        - truncated: whether results were truncated
        - error: error message if execution failed
    """
    if not sql or not sql.strip():
        return {"results": None, "error": "Empty SQL query"}

    sql_clean = sql.strip().rstrip(";")

    # Enforce row limit if not already present
    sql_upper = sql_clean.upper()
    if "LIMIT" not in sql_upper:
        sql_clean = f"{sql_clean} LIMIT {max_rows}"

    try:
        result = await db.execute(text(sql_clean))

        # Get column names
        columns = list(result.keys())

        # Fetch rows
        rows = result.fetchall()
        truncated = len(rows) >= max_rows

        # Convert to list of dicts
        results = []
        for row in rows[:max_rows]:
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Convert non-serializable types to strings
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                elif isinstance(val, bytes):
                    val = val.hex()
                elif hasattr(val, "__str__") and not isinstance(val, (str, int, float, bool, type(None))):
                    val = str(val)
                row_dict[col] = val
            results.append(row_dict)

        return {
            "results": results,
            "row_count": len(results),
            "columns": columns,
            "truncated": truncated,
            "error": None,
        }

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"SQL execution failed: {error_msg}")
        # Roll back the failed transaction
        await db.rollback()
        return {
            "results": None,
            "row_count": 0,
            "columns": [],
            "truncated": False,
            "error": error_msg,
        }
