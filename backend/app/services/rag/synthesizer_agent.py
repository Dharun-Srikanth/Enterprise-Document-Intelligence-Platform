"""
Synthesizer Agent — cross-document reasoning, citation, confidence.

Takes retrieved chunks and produces a grounded answer with:
- Source citations (document + section)
- Confidence score
- "Not found" handling for out-of-corpus queries
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SourceReference:
    document_id: str
    filename: str
    section: str
    chunk_text_preview: str  # first ~200 chars
    relevance_score: float


@dataclass
class SynthesisResult:
    question: str
    answer: str | None
    sources: list[SourceReference]
    confidence: float
    reasoning_notes: str | None = None
    not_found: bool = False
    partial: bool = False
    error: str | None = None


def synthesize(
    question: str,
    chunks: list,
    sub_queries: list[str] | None = None,
) -> SynthesisResult:
    """
    Synthesize an answer from retrieved chunks using LLM.

    Handles:
    - No relevant chunks → "information not found"
    - Partial evidence → answer with caveats
    - Full evidence → confident answer with citations
    """
    # Handle empty results
    if not chunks:
        return SynthesisResult(
            question=question,
            answer=None,
            sources=[],
            confidence=0.0,
            not_found=True,
            reasoning_notes="No relevant documents found in the corpus for this question.",
        )

    # Check if chunks have meaningful relevance
    avg_relevance = sum(c.relevance_score for c in chunks) / len(chunks)
    max_relevance = max(c.relevance_score for c in chunks)

    if max_relevance < 0.3:
        return SynthesisResult(
            question=question,
            answer=None,
            sources=[],
            confidence=0.0,
            not_found=True,
            reasoning_notes=(
                "Retrieved documents have very low relevance scores. "
                "The information may not exist in the ingested documents."
            ),
        )

    # Build context from chunks
    context_parts = []
    source_refs = []
    seen_sources = set()

    for i, chunk in enumerate(chunks[:8]):  # Limit context window
        label = f"[Source {i+1}: {chunk.filename}"
        if chunk.section:
            label += f" — {chunk.section}"
        label += f" (relevance: {chunk.relevance_score:.2f})]"

        context_parts.append(f"{label}\n{chunk.chunk_text}")

        src_key = (chunk.document_id, chunk.section)
        if src_key not in seen_sources:
            seen_sources.add(src_key)
            source_refs.append(SourceReference(
                document_id=chunk.document_id,
                filename=chunk.filename,
                section=chunk.section,
                chunk_text_preview=chunk.chunk_text[:200],
                relevance_score=chunk.relevance_score,
            ))

    context = "\n\n---\n\n".join(context_parts)

    # LLM synthesis
    try:
        from app.services.llm_client import chat_completion_json

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an enterprise document intelligence analyst. "
                    "Answer the user's question based ONLY on the provided source documents. "
                    "Return a JSON object with these fields:\n"
                    "- \"answer\": A comprehensive answer grounded in the sources. Cite sources as [Source N]. "
                    "If the sources don't contain the answer, say so clearly.\n"
                    "- \"confidence\": A float 0.0-1.0 indicating how well the sources answer the question. "
                    "1.0 = fully answered with strong evidence, 0.5 = partially answered, 0.0 = not answerable.\n"
                    "- \"reasoning\": Brief notes on what evidence was used and any gaps.\n"
                    "- \"is_partial\": boolean — true if only part of the question can be answered.\n\n"
                    "Rules:\n"
                    "- NEVER make up information not in the sources\n"
                    "- If evidence is weak or contradictory, lower confidence and note it\n"
                    "- Cite specific source numbers when making claims\n"
                    "- If the question cannot be answered from these documents, say so explicitly"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Source Documents:\n\n{context}"
                ),
            },
        ]

        result = chat_completion_json(
            messages, model="gpt-4o-mini", temperature=0.1, max_tokens=2000
        )

        answer = result.get("answer", "")
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "")
        is_partial = result.get("is_partial", False)

        # Adjust confidence based on retrieval quality
        retrieval_factor = min(1.0, avg_relevance * 1.5)
        adjusted_confidence = confidence * 0.7 + retrieval_factor * 0.3

        # Detect "not found" answers
        not_found = False
        not_found_phrases = [
            "not found in the", "no information", "cannot be answered",
            "not mentioned in", "no relevant data", "does not contain",
        ]
        if any(phrase in answer.lower() for phrase in not_found_phrases):
            not_found = True
            adjusted_confidence = min(adjusted_confidence, 0.1)

        return SynthesisResult(
            question=question,
            answer=answer,
            sources=source_refs,
            confidence=round(adjusted_confidence, 3),
            reasoning_notes=reasoning,
            not_found=not_found,
            partial=is_partial,
        )

    except Exception as e:
        logger.exception(f"Synthesis failed: {e}")
        return SynthesisResult(
            question=question,
            answer=None,
            sources=source_refs,
            confidence=0.0,
            error=f"LLM synthesis failed after retries: {str(e)}",
        )
