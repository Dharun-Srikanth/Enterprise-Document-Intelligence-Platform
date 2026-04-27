"""
NL-to-SQL Generator — translates natural language to SQL using LLM.

Provides the DB schema as context so the LLM generates valid queries
against the actual tables and columns.
"""

import logging

logger = logging.getLogger(__name__)

# Schema context provided to the LLM — describes all queryable tables
DB_SCHEMA_CONTEXT = """
Database: Enterprise Document Intelligence Platform (PostgreSQL)

TABLE documents (
    id UUID PRIMARY KEY,
    filename VARCHAR(500),        -- original file name
    file_type VARCHAR(50),        -- 'digital_doc', 'scanned_doc', 'component_photo'
    mime_type VARCHAR(100),
    doc_category VARCHAR(50),     -- 'Financial Report', 'Meeting Notes', 'Project Update', 'Executive Summary'
    doc_category_secondary VARCHAR(50),
    category_confidence FLOAT,    -- 0.0-1.0
    clean_text TEXT,              -- extracted/OCR'd text
    ocr_confidence FLOAT,         -- 0.0-1.0, NULL for digital docs
    processing_status VARCHAR(20), -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP
)

TABLE entities (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    entity_type VARCHAR(50),      -- 'PERSON', 'ORG', 'DATE', 'MONEY', 'PROJECT'
    entity_value TEXT,            -- raw entity text
    normalized_value TEXT,        -- normalized form
    confidence FLOAT,             -- 0.0-1.0
    created_at TIMESTAMP
)

TABLE entity_relationships (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    source_entity_id UUID REFERENCES entities(id),
    target_entity_id UUID REFERENCES entities(id),
    relationship_type VARCHAR(100), -- 'works_on', 'has_budget', 'manages', 'leads', etc.
    confidence FLOAT,
    created_at TIMESTAMP
)

TABLE components (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    component_type VARCHAR(100),  -- 'seat_track_assembly', 'recliner_mechanism', etc.
    component_confidence FLOAT,
    material VARCHAR(100),        -- 'cold_rolled_steel', 'HSLA_steel', etc.
    material_confidence FLOAT,
    estimated_cost_low DECIMAL(12,2),  -- USD
    estimated_cost_high DECIMAL(12,2),
    estimated_cost_mid DECIMAL(12,2),
    carbon_footprint_kg_co2e DECIMAL(10,4),
    emission_factor_source VARCHAR(200),
    overall_confidence FLOAT,
    is_flagged BOOLEAN,           -- TRUE if low confidence
    flag_reason TEXT,
    created_at TIMESTAMP
)

TABLE benchmark_data (
    id SERIAL PRIMARY KEY,
    component_type VARCHAR(100),
    material VARCHAR(100),
    cost_low DECIMAL(12,2),
    cost_high DECIMAL(12,2),
    cost_unit VARCHAR(20),        -- 'USD'
    carbon_footprint_kg_co2e DECIMAL(10,4),
    emission_factor_source VARCHAR(200),
    notes TEXT
)

TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    chunk_index INT,
    chunk_text TEXT,
    chunk_metadata JSONB,         -- {"section": "...", ...}
    created_at TIMESTAMP
)

Common query patterns:
- Join documents + entities to find entities in specific document types
- Join components + benchmark_data to compare estimated vs benchmark costs
- Aggregate components by type/material for cost and carbon analysis
- Filter entities by type to find people, orgs, projects, monetary values
- Use entity_relationships to find who works on what project
"""


def generate_sql(question: str, max_retries: int = 2) -> dict:
    """
    Generate SQL from a natural language question.

    Returns dict with:
    - sql: the generated SQL query
    - assumptions: list of assumptions made
    - error: error message if generation failed
    """
    from app.services.llm_client import chat_completion_json

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert SQL developer. Generate a PostgreSQL SELECT query "
                "to answer the user's question based on the database schema below.\n\n"
                f"{DB_SCHEMA_CONTEXT}\n\n"
                "Rules:\n"
                "- Generate ONLY SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE.\n"
                "- Use proper JOINs when combining tables\n"
                "- Use meaningful column aliases\n"
                "- Handle NULL values appropriately\n"
                "- Limit results to 100 rows max unless the user asks for all\n"
                "- If the question is ambiguous, make reasonable assumptions\n\n"
                "Return a JSON object with:\n"
                "- \"sql\": the SQL query string (single query, no semicolons)\n"
                "- \"assumptions\": array of strings describing assumptions you made\n"
                "- \"explanation\": brief explanation of what the query does"
            ),
        },
        {"role": "user", "content": question},
    ]

    try:
        result = chat_completion_json(
            messages, temperature=0.0, max_tokens=1500
        )

        sql = result.get("sql", "").strip().rstrip(";")
        assumptions = result.get("assumptions", [])

        if not sql:
            return {
                "sql": None,
                "assumptions": assumptions,
                "error": "LLM returned empty SQL",
            }

        return {
            "sql": sql,
            "assumptions": assumptions,
            "error": None,
        }

    except Exception as e:
        logger.exception(f"SQL generation failed: {e}")
        return {
            "sql": None,
            "assumptions": [],
            "error": f"SQL generation failed: {str(e)}",
        }


def regenerate_sql(question: str, failed_sql: str, error_message: str) -> dict:
    """
    Retry SQL generation with error feedback.
    Used when the first generated query fails validation or execution.
    """
    from app.services.llm_client import chat_completion_json

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert SQL developer. Your previous SQL query had an error. "
                "Fix the query based on the error message.\n\n"
                f"Database Schema:\n{DB_SCHEMA_CONTEXT}\n\n"
                "Rules:\n"
                "- Generate ONLY SELECT statements\n"
                "- Fix the specific error mentioned\n"
                "- Return valid PostgreSQL syntax\n\n"
                "Return a JSON object with:\n"
                "- \"sql\": the corrected SQL query\n"
                "- \"assumptions\": array of assumptions\n"
                "- \"explanation\": what you changed"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original question: {question}\n\n"
                f"Failed SQL:\n{failed_sql}\n\n"
                f"Error: {error_message}\n\n"
                "Please generate a corrected query."
            ),
        },
    ]

    try:
        result = chat_completion_json(
            messages, temperature=0.0, max_tokens=1500
        )

        sql = result.get("sql", "").strip().rstrip(";")
        assumptions = result.get("assumptions", [])

        return {
            "sql": sql if sql else None,
            "assumptions": assumptions,
            "error": None if sql else "LLM returned empty SQL on retry",
        }

    except Exception as e:
        logger.exception(f"SQL regeneration failed: {e}")
        return {
            "sql": None,
            "assumptions": [],
            "error": f"SQL regeneration failed: {str(e)}",
        }
