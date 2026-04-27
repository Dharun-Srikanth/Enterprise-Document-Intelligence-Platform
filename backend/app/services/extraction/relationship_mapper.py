"""Relationship mapping between extracted entities using LLM."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EntityRelation:
    source_type: str
    source_value: str
    target_type: str
    target_value: str
    relationship_type: str  # works_on, has_budget, manages, leads, etc.
    confidence: float = 0.0


def extract_relationships(
    text: str,
    entities: list[dict],
) -> list[EntityRelation]:
    """
    Extract relationships between entities found in the document.

    Args:
        text: Document text
        entities: List of entity dicts with 'entity_type' and 'value' keys
    """
    if not text or not entities or len(entities) < 2:
        return []

    try:
        return _llm_extract_relationships(text, entities)
    except Exception as e:
        logger.warning(f"LLM relationship extraction failed: {e}")
        return []


def _llm_extract_relationships(text: str, entities: list[dict]) -> list[EntityRelation]:
    """Use LLM to find relationships between entities."""
    from app.services.llm_client import chat_completion_json

    # Format entities for prompt
    entity_list = "\n".join(
        f"- {e['entity_type']}: {e['value']}"
        for e in entities[:50]  # Limit to avoid context overflow
    )

    max_chars = 4000
    truncated = text[:max_chars] if len(text) > max_chars else text

    prompt = f"""Given these entities extracted from a document:

{entity_list}

And the document text:
{truncated}

Find relationships between these entities. Return JSON:
{{
  "relationships": [
    {{
      "source_type": "entity type",
      "source_value": "entity value",
      "target_type": "entity type",
      "target_value": "entity value",
      "relationship": "works_on|has_budget|manages|leads|member_of|reports_to|supplies|associated_with",
      "confidence": 0.0 to 1.0
    }}
  ]
}}

Rules:
- Only include relationships clearly supported by the text
- Use these relationship types: works_on, has_budget, manages, leads, member_of, reports_to, supplies, associated_with
- Each relationship should connect two different entities from the list above
- Maximum 15 most important relationships"""

    result = chat_completion_json(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1500,
    )

    relations = []
    for rel in result.get("relationships", []):
        relations.append(EntityRelation(
            source_type=rel.get("source_type", ""),
            source_value=rel.get("source_value", ""),
            target_type=rel.get("target_type", ""),
            target_value=rel.get("target_value", ""),
            relationship_type=rel.get("relationship", "associated_with"),
            confidence=float(rel.get("confidence", 0.5)),
        ))

    return relations
