"""
Retriever Agent — query decomposition, vector search, ranking.

Decomposes complex questions into sub-queries, searches ChromaDB
for each, then ranks and deduplicates the results.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_text: str
    document_id: str
    filename: str
    file_type: str
    doc_category: str
    chunk_index: int
    section: str
    relevance_score: float  # 1 - distance (cosine)
    sub_query: str  # which sub-query retrieved this


@dataclass
class RetrievalResult:
    original_question: str
    sub_queries: list[str]
    chunks: list[RetrievedChunk]
    total_chunks_searched: int = 0
    error: str | None = None


def decompose_query(question: str) -> list[str]:
    """
    Use LLM to decompose a complex question into atomic sub-queries
    for more targeted vector search.
    """
    try:
        from app.services.llm_client import chat_completion_json

        messages = [
            {
                "role": "system",
                "content": (
                    "You decompose complex questions into simpler sub-queries for document search. "
                    "Return a JSON object with a 'sub_queries' array of strings. "
                    "Rules:\n"
                    "- If the question is already simple, return it as the only sub-query\n"
                    "- Create 2-4 sub-queries max\n"
                    "- Each sub-query should target a specific piece of information\n"
                    "- Sub-queries should be self-contained (understandable without the original)\n"
                    "- Focus on the key entities, metrics, and relationships in the question"
                ),
            },
            {"role": "user", "content": f"Decompose this question:\n\n{question}"},
        ]

        result = chat_completion_json(messages, model="gpt-4o-mini", temperature=0.0, max_tokens=500)
        sub_queries = result.get("sub_queries", [question])

        if not sub_queries:
            return [question]

        logger.info(f"Decomposed into {len(sub_queries)} sub-queries: {sub_queries}")
        return sub_queries

    except Exception as e:
        logger.warning(f"Query decomposition failed, using original: {e}")
        return [question]


def search_vectors(
    query_text: str,
    collection_name: str = "documents",
    n_results: int = 5,
) -> list[dict]:
    """
    Embed a query and search ChromaDB for similar chunks.
    Returns raw ChromaDB results.
    """
    from app.services.llm_client import get_embeddings
    from app.db.vector_store import get_collection

    # Get query embedding
    embeddings = get_embeddings([query_text])
    query_embedding = embeddings[0]

    # Search ChromaDB
    collection = get_collection(collection_name)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    return results


def retrieve(question: str, top_k: int = 10) -> RetrievalResult:
    """
    Full retrieval pipeline:
    1. Decompose question into sub-queries
    2. Vector search for each sub-query
    3. Rank, deduplicate, return top-k chunks
    """
    # Step 1: Decompose
    sub_queries = decompose_query(question)

    all_chunks: list[RetrievedChunk] = []
    seen_chunk_ids: set[str] = set()
    total_searched = 0

    # Step 2: Search per sub-query
    per_query_k = max(5, top_k // len(sub_queries) + 2)

    for sq in sub_queries:
        try:
            results = search_vectors(sq, n_results=per_query_k)

            ids = results.get("ids", [[]])[0]
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            total_searched += len(ids)

            for i, chunk_id in enumerate(ids):
                if chunk_id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(chunk_id)

                meta = metas[i] if i < len(metas) else {}
                relevance = 1.0 - (distances[i] if i < len(distances) else 0.5)

                all_chunks.append(RetrievedChunk(
                    chunk_text=docs[i] if i < len(docs) else "",
                    document_id=meta.get("document_id", ""),
                    filename=meta.get("filename", ""),
                    file_type=meta.get("file_type", ""),
                    doc_category=meta.get("doc_category", ""),
                    chunk_index=meta.get("chunk_index", 0),
                    section=meta.get("section", ""),
                    relevance_score=max(0.0, min(1.0, relevance)),
                    sub_query=sq,
                ))

        except Exception as e:
            logger.warning(f"Vector search failed for sub-query '{sq}': {e}")

    # Step 3: Rank by relevance (descending) and take top-k
    all_chunks.sort(key=lambda c: c.relevance_score, reverse=True)
    top_chunks = all_chunks[:top_k]

    return RetrievalResult(
        original_question=question,
        sub_queries=sub_queries,
        chunks=top_chunks,
        total_chunks_searched=total_searched,
    )
