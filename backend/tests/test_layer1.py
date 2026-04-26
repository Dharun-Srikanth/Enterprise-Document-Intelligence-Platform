"""
Local test script for Layer 1 — Document Ingestion & OCR.
Runs directly without the API/DB stack.

Usage: python -m tests.test_layer1
"""

import os
import sys
import json

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ingestion.detector import detect_input_type, InputType
from app.services.ingestion.pipeline import process_document

TEST_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")


def test_detection():
    """Test input type auto-detection."""
    print("=" * 60)
    print("TEST: Input Type Detection")
    print("=" * 60)

    # Digital docs
    digital_dir = os.path.join(TEST_DATA, "digital")
    if os.path.exists(digital_dir):
        for f in os.listdir(digital_dir):
            fpath = os.path.join(digital_dir, f)
            if os.path.isfile(fpath) and not f.startswith("."):
                result = detect_input_type(fpath)
                status = "PASS" if result == InputType.DIGITAL_DOC else "FAIL"
                print(f"  [{status}] {f} → {result.value}")

    # Scanned docs
    scanned_dir = os.path.join(TEST_DATA, "scanned")
    if os.path.exists(scanned_dir):
        for f in os.listdir(scanned_dir):
            fpath = os.path.join(scanned_dir, f)
            if os.path.isfile(fpath) and not f.startswith("."):
                result = detect_input_type(fpath)
                status = "PASS" if result == InputType.SCANNED_DOC else "WARN"
                print(f"  [{status}] {f} → {result.value}")

    # Teardown photos
    teardown_dir = os.path.join(TEST_DATA, "teardown")
    if os.path.exists(teardown_dir):
        for f in os.listdir(teardown_dir):
            fpath = os.path.join(teardown_dir, f)
            if os.path.isfile(fpath) and not f.startswith("."):
                result = detect_input_type(fpath)
                status = "PASS" if result == InputType.COMPONENT_PHOTO else "WARN"
                print(f"  [{status}] {f} → {result.value}")

    print()


def test_processing():
    """Test full processing pipeline for each file type."""
    print("=" * 60)
    print("TEST: Full Processing Pipeline")
    print("=" * 60)

    test_files = []

    # Collect all test files
    for subdir in ["digital", "scanned", "teardown"]:
        dirpath = os.path.join(TEST_DATA, subdir)
        if os.path.exists(dirpath):
            for f in os.listdir(dirpath):
                fpath = os.path.join(dirpath, f)
                if os.path.isfile(fpath) and not f.startswith("."):
                    test_files.append((subdir, f, fpath))

    for category, filename, filepath in test_files:
        print(f"\n  Processing: [{category}] {filename}")
        result = process_document(filepath)
        print(f"    Type:       {result.input_type}")
        print(f"    Text len:   {len(result.clean_text)} chars")
        print(f"    Confidence: {result.ocr_confidence}")
        print(f"    Has image:  {result.image_base64 is not None}")
        print(f"    Error:      {result.error}")

        if result.tables:
            print(f"    Tables:     {len(result.tables)} detected")
            for i, table in enumerate(result.tables):
                print(f"      Table {i+1}: {len(table)} rows")

        if result.structure_metadata:
            headings = result.structure_metadata.get("headings", [])
            if headings:
                print(f"    Headings:   {headings[:5]}{'...' if len(headings) > 5 else ''}")

        if result.clean_text:
            preview = result.clean_text[:200].replace("\n", " ")
            print(f"    Preview:    {preview}...")

    print()


def test_summary():
    """Print a summary of all test data files."""
    print("=" * 60)
    print("TEST DATA SUMMARY")
    print("=" * 60)

    for subdir in ["digital", "scanned", "teardown"]:
        dirpath = os.path.join(TEST_DATA, subdir)
        if os.path.exists(dirpath):
            files = [f for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f)) and not f.startswith(".")]
            print(f"\n  {subdir}/: {len(files)} files")
            for f in sorted(files):
                size = os.path.getsize(os.path.join(dirpath, f))
                print(f"    {f} ({size/1024:.1f} KB)")

    benchmark = os.path.join(TEST_DATA, "benchmark.csv")
    if os.path.exists(benchmark):
        with open(benchmark) as f:
            lines = f.readlines()
        print(f"\n  benchmark.csv: {len(lines)-1} entries")

    print()


if __name__ == "__main__":
    test_summary()
    test_detection()
    test_processing()
    print("All Layer 1 tests complete!")
