"""Entity extraction using spaCy NER + LLM refinement."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    entity_type: str  # PERSON, ORG, DATE, MONEY, PROJECT
    value: str
    normalized_value: str | None = None
    confidence: float = 0.0
    start_offset: int | None = None
    end_offset: int | None = None


def extract_entities(text: str, use_llm: bool = True) -> list[ExtractedEntity]:
    """
    Extract named entities from document text.

    1. spaCy NER for baseline (PERSON, ORG, DATE, MONEY)
    2. LLM pass for PROJECT names and normalization
    """
    if not text or not text.strip():
        return []

    # Step 1: spaCy baseline
    entities = _spacy_extract(text)

    # Step 2: LLM refinement for projects + normalization
    if use_llm:
        try:
            llm_entities = _llm_extract(text)
            entities = _merge_entities(entities, llm_entities)
        except Exception as e:
            logger.warning(f"LLM entity extraction failed, using spaCy only: {e}")

    return entities


def _spacy_extract(text: str) -> list[ExtractedEntity]:
    """Extract entities using spaCy."""
    import spacy

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.error("spaCy model 'en_core_web_sm' not found")
        return []

    doc = nlp(text)
    entities = []

    type_map = {
        "PERSON": "PERSON",
        "ORG": "ORG",
        "DATE": "DATE",
        "MONEY": "MONEY",
        "GPE": "ORG",  # Map geopolitical entities to ORG for simplicity
    }

    seen = set()
    for ent in doc.ents:
        mapped_type = type_map.get(ent.label_)
        if not mapped_type:
            continue

        value = ent.text.strip()
        if not value or len(value) < 2:
            continue

        key = (mapped_type, value.lower())
        if key in seen:
            continue
        seen.add(key)

        normalized = _normalize_entity(mapped_type, value)

        entities.append(ExtractedEntity(
            entity_type=mapped_type,
            value=value,
            normalized_value=normalized,
            confidence=0.75,  # spaCy baseline confidence
            start_offset=ent.start_char,
            end_offset=ent.end_char,
        ))

    return entities


def _llm_extract(text: str) -> list[ExtractedEntity]:
    """Extract entities using LLM — especially project/initiative names."""
    from app.services.llm_client import chat_completion_json

    # Truncate text if too long for context
    max_chars = 6000
    truncated = text[:max_chars] if len(text) > max_chars else text

    prompt = f"""Extract named entities from this document text. Return JSON with this exact structure:
{{
  "entities": [
    {{
      "type": "PERSON|ORG|DATE|MONEY|PROJECT",
      "value": "exact text from document",
      "normalized": "normalized form (ISO date, USD amount, clean name)"
    }}
  ]
}}

Rules:
- PERSON: Full names of people mentioned
- ORG: Company names, organization names
- DATE: Any dates mentioned (normalize to ISO 8601: YYYY-MM-DD)
- MONEY: Monetary amounts (normalize to USD number, e.g. "$1.5M" → "1500000")
- PROJECT: Project names, program names, initiative names (e.g. "COSIP", "STA-R2")

Only extract entities that are clearly present. Do not invent entities.

Document text:
{truncated}"""

    result = chat_completion_json(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2000,
    )

    entities = []
    for ent in result.get("entities", []):
        etype = ent.get("type", "").upper()
        if etype not in ("PERSON", "ORG", "DATE", "MONEY", "PROJECT"):
            continue

        entities.append(ExtractedEntity(
            entity_type=etype,
            value=ent.get("value", ""),
            normalized_value=ent.get("normalized"),
            confidence=0.85,  # LLM confidence
        ))

    return entities


def _merge_entities(spacy_ents: list[ExtractedEntity], llm_ents: list[ExtractedEntity]) -> list[ExtractedEntity]:
    """Merge spaCy and LLM entities, preferring LLM for overlaps."""
    merged = {}

    # Add spaCy entities first
    for ent in spacy_ents:
        key = (ent.entity_type, ent.value.lower().strip())
        merged[key] = ent

    # Add/override with LLM entities
    for ent in llm_ents:
        key = (ent.entity_type, ent.value.lower().strip())
        if key in merged:
            # Keep LLM normalized value but retain spaCy offsets
            existing = merged[key]
            existing.normalized_value = ent.normalized_value or existing.normalized_value
            existing.confidence = max(existing.confidence, ent.confidence)
        else:
            merged[key] = ent

    return list(merged.values())


def _normalize_entity(entity_type: str, value: str) -> str | None:
    """Basic normalization for common entity types."""
    if entity_type == "MONEY":
        # Try to extract numeric value
        import re
        cleaned = value.replace(",", "").replace("$", "").strip()
        # Handle M/B suffixes
        match = re.search(r"([\d.]+)\s*([MBKmb])", cleaned)
        if match:
            num = float(match.group(1))
            suffix = match.group(2).upper()
            multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
            return str(num * multipliers.get(suffix, 1))
        try:
            return str(float(cleaned))
        except ValueError:
            pass

    return None
