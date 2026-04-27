"""Document classification using LLM."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DOCUMENT_CATEGORIES = [
    "Financial Report",
    "Meeting Notes",
    "Project Update",
    "Executive Summary",
]


@dataclass
class ClassificationResult:
    primary_category: str
    primary_confidence: float
    secondary_category: str | None = None
    secondary_confidence: float | None = None
    reasoning: str | None = None


def classify_document(text: str) -> ClassificationResult:
    """
    Classify a document into one of the defined categories.
    Returns primary + secondary classification with confidence scores.
    """
    if not text or not text.strip():
        return ClassificationResult(
            primary_category="Unknown",
            primary_confidence=0.0,
        )

    try:
        return _llm_classify(text)
    except Exception as e:
        logger.warning(f"LLM classification failed, using heuristic: {e}")
        return _heuristic_classify(text)


def _llm_classify(text: str) -> ClassificationResult:
    """Classify document using LLM."""
    from app.services.llm_client import chat_completion_json

    # Truncate for context window
    max_chars = 4000
    truncated = text[:max_chars] if len(text) > max_chars else text

    prompt = f"""Classify this document into one of these categories:
1. Financial Report — budgets, revenue, costs, financial summaries
2. Meeting Notes — meeting minutes, agendas, action items, attendee lists
3. Project Update — project status reports, milestone tracking, progress updates
4. Executive Summary — strategy briefs, high-level overviews, board communications

Return JSON:
{{
  "primary_category": "one of the four categories above",
  "primary_confidence": 0.0 to 1.0,
  "secondary_category": "another category if applicable, or null",
  "secondary_confidence": 0.0 to 1.0 or null,
  "reasoning": "brief explanation of why this classification"
}}

Document text:
{truncated}"""

    result = chat_completion_json(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500,
    )

    return ClassificationResult(
        primary_category=result.get("primary_category", "Unknown"),
        primary_confidence=float(result.get("primary_confidence", 0.0)),
        secondary_category=result.get("secondary_category"),
        secondary_confidence=float(result["secondary_confidence"]) if result.get("secondary_confidence") else None,
        reasoning=result.get("reasoning"),
    )


def _heuristic_classify(text: str) -> ClassificationResult:
    """Fallback heuristic classification based on keyword matching."""
    text_lower = text.lower()

    scores = {
        "Financial Report": 0,
        "Meeting Notes": 0,
        "Project Update": 0,
        "Executive Summary": 0,
    }

    # Financial keywords
    for kw in ["revenue", "budget", "cost", "financial", "capex", "savings", "expenditure", "margin", "profit", "quarterly"]:
        if kw in text_lower:
            scores["Financial Report"] += 1

    # Meeting keywords
    for kw in ["attendees", "agenda", "action items", "meeting", "minutes", "sprint", "retrospective", "facilitator"]:
        if kw in text_lower:
            scores["Meeting Notes"] += 1

    # Project update keywords
    for kw in ["milestone", "status", "progress", "workstream", "phase", "timeline", "deliverable", "blocker"]:
        if kw in text_lower:
            scores["Project Update"] += 1

    # Executive summary keywords
    for kw in ["strategy", "strategic", "board", "investment", "pillar", "recommendation", "governance", "vision"]:
        if kw in text_lower:
            scores["Executive Summary"] += 1

    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    total = sum(scores.values()) or 1

    primary = sorted_cats[0]
    secondary = sorted_cats[1] if sorted_cats[1][1] > 0 else None

    return ClassificationResult(
        primary_category=primary[0],
        primary_confidence=round(primary[1] / total, 2),
        secondary_category=secondary[0] if secondary else None,
        secondary_confidence=round(secondary[1] / total, 2) if secondary else None,
    )
