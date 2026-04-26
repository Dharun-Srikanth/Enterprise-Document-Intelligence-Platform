"""
Local test script for Milestone 3 — RAG + SQL Agent.
Tests components that don't need LLM or DB.

Usage: python -m tests.test_layer3
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_sql_validator():
    """Test SQL validation logic (no LLM needed)."""
    print("=" * 60)
    print("TEST: SQL Validator")
    print("=" * 60)

    from app.services.sql_agent.validator import validate_sql

    test_cases = [
        # (description, sql, should_be_valid)
        ("Valid SELECT", "SELECT * FROM documents", True),
        ("Valid JOIN", "SELECT d.filename, e.entity_value FROM documents d JOIN entities e ON d.id = e.document_id", True),
        ("Valid CTE", "WITH recent AS (SELECT * FROM documents WHERE created_at > '2025-01-01') SELECT * FROM recent", True),
        ("Valid aggregate", "SELECT component_type, AVG(estimated_cost_mid) FROM components GROUP BY component_type LIMIT 10", True),
        ("Block DROP", "DROP TABLE documents", False),
        ("Block DELETE", "DELETE FROM documents WHERE id = '123'", False),
        ("Block UPDATE", "UPDATE documents SET filename = 'hack' WHERE id = '123'", False),
        ("Block INSERT", "INSERT INTO documents (filename) VALUES ('test')", False),
        ("Block injection", "SELECT * FROM documents; DROP TABLE documents", False),
        ("Block ALTER", "ALTER TABLE documents ADD COLUMN hack TEXT", False),
        ("Block TRUNCATE", "TRUNCATE TABLE documents", False),
        ("Empty query", "", False),
        ("SELECT INTO blocked", "SELECT * INTO new_table FROM documents", False),
    ]

    passed = 0
    failed = 0
    for desc, sql, expected_valid in test_cases:
        result = validate_sql(sql)
        actual = result["valid"]
        status = "PASS" if actual == expected_valid else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {desc}")
        if actual != expected_valid:
            print(f"    Expected valid={expected_valid}, got valid={actual}")
            print(f"    Errors: {result['errors']}")
        if result["warnings"]:
            print(f"    Warnings: {result['warnings']}")

    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


def test_module_imports():
    """Test that all RAG and SQL agent modules import cleanly."""
    print("\n" + "=" * 60)
    print("TEST: Module Imports")
    print("=" * 60)

    modules = [
        "app.services.rag.retriever_agent",
        "app.services.rag.synthesizer_agent",
        "app.services.rag.orchestrator",
        "app.services.sql_agent.generator",
        "app.services.sql_agent.validator",
        "app.services.sql_agent.executor",
        "app.services.sql_agent.orchestrator",
    ]

    all_ok = True
    for mod in modules:
        try:
            __import__(mod)
            print(f"  [PASS] {mod}")
        except Exception as e:
            print(f"  [FAIL] {mod}: {e}")
            all_ok = False

    return all_ok


def test_retriever_decompose():
    """Test query decomposition (needs LLM)."""
    print("\n" + "=" * 60)
    print("TEST: Query Decomposition (LLM)")
    print("=" * 60)

    from app.services.rag.retriever_agent import decompose_query

    test_questions = [
        "Which cost-saving ideas also reduce carbon footprint?",
        "What is the total budget for the seat track assembly project?",
        "Compare the material costs across all tear-down components and identify which uses the most expensive materials",
    ]

    for q in test_questions:
        sub_queries = decompose_query(q)
        print(f"  Q: {q}")
        print(f"  Sub-queries ({len(sub_queries)}):")
        for sq in sub_queries:
            print(f"    - {sq}")
        print()

    return True


def test_sql_generator():
    """Test SQL generation (needs LLM)."""
    print("\n" + "=" * 60)
    print("TEST: SQL Generation (LLM)")
    print("=" * 60)

    from app.services.sql_agent.generator import generate_sql
    from app.services.sql_agent.validator import validate_sql

    test_questions = [
        "Total component cost for the seat track assembly?",
        "List all people mentioned in meeting notes",
        "Which components have the highest carbon footprint?",
        "Show all documents classified as financial reports",
    ]

    for q in test_questions:
        result = generate_sql(q)
        sql = result.get("sql", "None")
        assumptions = result.get("assumptions", [])
        error = result.get("error")

        print(f"  Q: {q}")
        if error:
            print(f"  [ERROR] {error}")
        else:
            print(f"  SQL: {sql}")
            if assumptions:
                print(f"  Assumptions: {assumptions}")

            # Validate the generated SQL
            validation = validate_sql(sql)
            v_status = "VALID" if validation["valid"] else "INVALID"
            print(f"  Validation: {v_status}")
            if validation["errors"]:
                print(f"  Val errors: {validation['errors']}")
        print()

    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" MILESTONE 3 TESTS — RAG + SQL Agent")
    print("=" * 60 + "\n")

    # Tests that don't need LLM or DB
    test_module_imports()
    test_sql_validator()

    # Tests that need OPENAI_API_KEY
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key and api_key != "your-openai-api-key-here":
        print("\n[LLM available — running LLM-dependent tests]\n")
        test_retriever_decompose()
        test_sql_generator()
    else:
        print("\n[SKIP] LLM tests — set OPENAI_API_KEY to run")
        print("  Skipped: Query Decomposition")
        print("  Skipped: SQL Generation")

    print("\nAll Milestone 3 tests complete!")
