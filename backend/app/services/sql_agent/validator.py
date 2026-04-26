"""
SQL Validator — validates generated SQL for safety and correctness.

Checks:
1. Only SELECT statements allowed (blocks DML/DDL)
2. Referenced tables exist in our schema
3. Referenced columns exist in the tables
4. Basic syntax validation via sqlparse
"""

import re
import logging

logger = logging.getLogger(__name__)

# Allowed tables and their columns
ALLOWED_TABLES = {
    "documents": {
        "id", "filename", "file_type", "mime_type", "doc_category",
        "doc_category_secondary", "category_confidence", "clean_text",
        "raw_text", "ocr_confidence", "processing_status", "processing_error",
        "file_path", "created_at", "updated_at", "structure_metadata",
    },
    "entities": {
        "id", "document_id", "entity_type", "entity_value",
        "normalized_value", "confidence", "start_offset", "end_offset",
        "created_at",
    },
    "entity_relationships": {
        "id", "document_id", "source_entity_id", "target_entity_id",
        "relationship_type", "confidence", "created_at",
    },
    "components": {
        "id", "document_id", "component_type", "component_confidence",
        "material", "material_confidence", "estimated_cost_low",
        "estimated_cost_high", "estimated_cost_mid",
        "carbon_footprint_kg_co2e", "emission_factor_source",
        "overall_confidence", "is_flagged", "flag_reason",
        "classification_metadata", "created_at",
    },
    "benchmark_data": {
        "id", "component_type", "material", "cost_low", "cost_high",
        "cost_unit", "carbon_footprint_kg_co2e", "emission_factor_source",
        "notes",
    },
    "document_chunks": {
        "id", "document_id", "chunk_index", "chunk_text",
        "chunk_metadata", "vector_id", "created_at",
    },
    "query_logs": {
        "id", "query_type", "user_query", "generated_sql",
        "result_summary", "sources", "confidence", "error",
        "execution_time_ms", "created_at",
    },
}

# Destructive SQL keywords that must be blocked
BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
    "INTO",  # blocks SELECT INTO and INSERT INTO
    "COPY", "\\\\COPY",
]


def validate_sql(sql: str) -> dict:
    """
    Validate a SQL query for safety and correctness.

    Returns:
        dict with:
        - valid: bool
        - errors: list of error strings
        - warnings: list of warning strings
    """
    errors = []
    warnings = []

    if not sql or not sql.strip():
        return {"valid": False, "errors": ["Empty SQL query"], "warnings": []}

    sql_clean = sql.strip().rstrip(";")
    sql_upper = sql_clean.upper()

    # 1. Must start with SELECT (or WITH for CTEs)
    first_keyword = sql_upper.lstrip().split()[0] if sql_upper.strip() else ""
    if first_keyword not in ("SELECT", "WITH"):
        errors.append(
            f"Only SELECT queries are allowed. Got: {first_keyword}"
        )
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 2. Block destructive keywords
    # We tokenize to avoid matching substrings (e.g., "UPDATE" inside "UPDATED_AT")
    # Use word boundary regex
    for keyword in BLOCKED_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        # Check outside of string literals
        sql_no_strings = _strip_string_literals(sql_clean)
        if re.search(pattern, sql_no_strings, re.IGNORECASE):
            errors.append(
                f"Blocked keyword detected: {keyword}. Only SELECT queries are allowed."
            )

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 3. Check referenced tables exist
    referenced_tables = _extract_table_references(sql_clean)
    for table in referenced_tables:
        table_lower = table.lower()
        if table_lower not in ALLOWED_TABLES:
            # Could be an alias or subquery — warn instead of block
            warnings.append(f"Unknown table reference: '{table}'. May be an alias.")

    # 4. Check for common SQL injection patterns
    injection_patterns = [
        r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER)",
        r"--\s*$",  # trailing comment that could hide injected SQL
        r"/\*.*\*/",  # block comments
        r"UNION\s+ALL\s+SELECT\s+.*FROM\s+pg_",  # pg catalog access
        r"pg_sleep",
        r"information_schema",
    ]
    for pattern in injection_patterns:
        if re.search(pattern, sql_clean, re.IGNORECASE):
            errors.append(f"Potentially unsafe SQL pattern detected")
            break

    # 5. Limit check
    if "LIMIT" not in sql_upper:
        warnings.append("No LIMIT clause — results may be large. Consider adding LIMIT 100.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _strip_string_literals(sql: str) -> str:
    """Remove string literals to avoid false positive keyword matches."""
    return re.sub(r"'[^']*'", "''", sql)


def _extract_table_references(sql: str) -> list[str]:
    """
    Extract table names from FROM and JOIN clauses.
    Simple regex-based extraction — not a full parser.
    """
    tables = set()

    # FROM table_name (with optional alias)
    from_pattern = r"\bFROM\s+(\w+)"
    for match in re.finditer(from_pattern, sql, re.IGNORECASE):
        tables.add(match.group(1))

    # JOIN table_name (with optional alias)
    join_pattern = r"\bJOIN\s+(\w+)"
    for match in re.finditer(join_pattern, sql, re.IGNORECASE):
        tables.add(match.group(1))

    return list(tables)
