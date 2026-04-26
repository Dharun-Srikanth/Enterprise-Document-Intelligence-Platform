"""
Local test script for Layer 2 — Extraction, Classification & Storage.
Tests individual components without DB. LLM tests require OPENAI_API_KEY.

Usage: python -m tests.test_layer2
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Load a sample document for testing
def _load_test_doc(filename: str) -> str:
    path = os.path.join(TEST_DATA, "digital", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_entity_extraction_spacy():
    """Test spaCy-only entity extraction (no LLM needed)."""
    print("=" * 60)
    print("TEST: Entity Extraction (spaCy only)")
    print("=" * 60)

    from app.services.extraction.entity_extractor import extract_entities

    text = _load_test_doc("financial_summary_q3_2025.txt")
    entities = extract_entities(text, use_llm=False)

    print(f"  Found {len(entities)} entities:")
    by_type = {}
    for e in entities:
        by_type.setdefault(e.entity_type, []).append(e.value)
    for etype, values in sorted(by_type.items()):
        print(f"    {etype}: {values[:5]}{'...' if len(values) > 5 else ''}")
    print()
    return len(entities) > 0


def test_entity_extraction_llm():
    """Test LLM-enhanced entity extraction."""
    print("=" * 60)
    print("TEST: Entity Extraction (spaCy + LLM)")
    print("=" * 60)

    from app.services.extraction.entity_extractor import extract_entities

    text = _load_test_doc("meeting_notes_sprint8.txt")
    entities = extract_entities(text, use_llm=True)

    print(f"  Found {len(entities)} entities:")
    by_type = {}
    for e in entities:
        by_type.setdefault(e.entity_type, []).append(f"{e.value} (conf={e.confidence})")
    for etype, values in sorted(by_type.items()):
        print(f"    {etype}:")
        for v in values[:8]:
            print(f"      - {v}")
    print()
    return len(entities) > 0


def test_document_classification():
    """Test document classification on all 5 digital docs."""
    print("=" * 60)
    print("TEST: Document Classification")
    print("=" * 60)

    from app.services.extraction.doc_classifier import classify_document

    expected = {
        "financial_summary_q3_2025.txt": "Financial Report",
        "meeting_notes_sprint8.txt": "Meeting Notes",
        "project_update_cosip_aug2025.txt": "Project Update",
        "strategy_brief_sustainability.txt": "Executive Summary",
        "project_spec_seat_track.txt": "Project Update",  # Could also be Executive Summary
    }

    for filename, expected_cat in expected.items():
        text = _load_test_doc(filename)
        result = classify_document(text)
        match = "PASS" if result.primary_category == expected_cat else "WARN"
        print(f"  [{match}] {filename}")
        print(f"    Primary:   {result.primary_category} ({result.primary_confidence:.2f})")
        if result.secondary_category:
            print(f"    Secondary: {result.secondary_category} ({result.secondary_confidence:.2f})")
        if result.reasoning:
            print(f"    Reason:    {result.reasoning[:100]}...")
    print()


def test_relationship_mapping():
    """Test relationship extraction between entities."""
    print("=" * 60)
    print("TEST: Relationship Mapping")
    print("=" * 60)

    from app.services.extraction.relationship_mapper import extract_relationships

    text = _load_test_doc("meeting_notes_sprint8.txt")
    entities = [
        {"entity_type": "PERSON", "value": "Raj Patel"},
        {"entity_type": "PERSON", "value": "David Park"},
        {"entity_type": "PERSON", "value": "Sarah Chen"},
        {"entity_type": "PERSON", "value": "Maria Santos"},
        {"entity_type": "ORG", "value": "Nexus Automotive Group"},
        {"entity_type": "ORG", "value": "TierOne Manufacturing"},
        {"entity_type": "ORG", "value": "SteelCraft Industries"},
        {"entity_type": "PROJECT", "value": "Seat Track Assembly Redesign"},
        {"entity_type": "PROJECT", "value": "COSIP"},
    ]

    relationships = extract_relationships(text, entities)

    print(f"  Found {len(relationships)} relationships:")
    for rel in relationships[:10]:
        print(f"    {rel.source_value} --[{rel.relationship_type}]--> {rel.target_value} (conf={rel.confidence})")
    print()
    return len(relationships) > 0


def test_sustainability_benchmark():
    """Test benchmark data lookup (no LLM needed)."""
    print("=" * 60)
    print("TEST: Sustainability Benchmark Lookup")
    print("=" * 60)

    from app.services.extraction.sustainability import estimate_sustainability, load_benchmark_data

    data = load_benchmark_data()
    print(f"  Loaded {len(data)} benchmark entries")

    test_cases = [
        ("seat_track_assembly", "cold_rolled_steel"),
        ("seat_track_assembly", "HSLA_steel"),
        ("recliner_mechanism", "cold_rolled_steel"),
        ("wire_spring_support", "spring_steel_wire"),
        ("unknown_component", "unknown_material"),
    ]

    for comp, mat in test_cases:
        est = estimate_sustainability(comp, mat)
        if est.match_found:
            print(f"  [MATCH] {comp} / {mat}")
            print(f"    Cost: ${est.cost_low}-${est.cost_high} (mid: ${est.cost_mid})")
            print(f"    Carbon: {est.carbon_footprint_kg_co2e} kg CO2e")
            print(f"    Source: {est.emission_factor_source}")
        else:
            print(f"  [NO MATCH] {comp} / {mat}: {est.notes}")
    print()
    return True


def test_chunking():
    """Test document chunking."""
    print("=" * 60)
    print("TEST: Document Chunking")
    print("=" * 60)

    from app.services.extraction.chunker import chunk_document

    for filename in ["financial_summary_q3_2025.txt", "meeting_notes_sprint8.txt"]:
        text = _load_test_doc(filename)
        # Simulate structure metadata with headings
        headings = [line.strip() for line in text.split("\n") if line.strip().isupper() and 3 < len(line.strip()) < 100]
        structure = {"headings": headings}

        chunks = chunk_document(text, structure)
        print(f"  {filename}: {len(chunks)} chunks")
        for c in chunks[:3]:
            section = c.metadata.get("section", "?")
            print(f"    Chunk {c.chunk_index}: [{section}] {len(c.text)} chars — {c.text[:80]}...")
        if len(chunks) > 3:
            print(f"    ... and {len(chunks) - 3} more")
    print()
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" LAYER 2 TESTS")
    print("=" * 60 + "\n")

    # Tests that don't need LLM
    test_chunking()
    test_sustainability_benchmark()
    test_entity_extraction_spacy()

    # Tests that need OPENAI_API_KEY
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key and api_key != "your-openai-api-key-here":
        print("[LLM available — running LLM-dependent tests]\n")
        test_entity_extraction_llm()
        test_document_classification()
        test_relationship_mapping()
    else:
        print("[SKIP] LLM tests — set OPENAI_API_KEY to run")
        print("  Skipped: Entity Extraction (LLM)")
        print("  Skipped: Document Classification (LLM)")
        print("  Skipped: Relationship Mapping (LLM)")

    print("\nAll Layer 2 tests complete!")
