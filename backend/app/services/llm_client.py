"""Groq LLM client (OpenAI-compatible API) + ChromaDB local embeddings."""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_client = None
_embedding_fn = None


# ---------------------------------------------------------------------------
# Groq client (OpenAI-compatible)
# ---------------------------------------------------------------------------

def _get_client():
    """Get or create Groq client via OpenAI SDK."""
    global _client
    if _client is None:
        from openai import OpenAI
        from app.config import get_settings
        settings = get_settings()
        api_key = settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        if not api_key or api_key == "your-groq-api-key-here":
            raise ValueError(
                "GROQ_API_KEY not set. Please set it in .env file. "
                "Get a free key at https://console.groq.com"
            )
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


# ---------------------------------------------------------------------------
# Chat completion
# ---------------------------------------------------------------------------

def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None,
    max_retries: int = 3,
) -> str:
    """
    Call Groq chat completion with retry logic.
    Uses OpenAI-compatible API format.
    """
    from app.config import get_settings
    client = _get_client()
    model = model or get_settings().llm_model

    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""

        except Exception as e:
            logger.warning(f"Groq API attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                raise
            import time
            time.sleep(2 ** attempt)

    return ""


def chat_completion_json(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2000,
    max_retries: int = 3,
) -> dict:
    """Call Groq and parse response as JSON."""
    raw = chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        max_retries=max_retries,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        return json.loads(raw)


# ---------------------------------------------------------------------------
# Vision completion
# ---------------------------------------------------------------------------

def vision_completion(
    image_data_url: str,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1500,
    max_retries: int = 3,
) -> str:
    """Call Groq vision model with an image (OpenAI-compatible format)."""
    from app.config import get_settings
    model = model or get_settings().llm_model_vision

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url},
                },
            ],
        }
    ]
    return chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
    )


def vision_completion_json(
    image_data_url: str,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1500,
    max_retries: int = 3,
) -> dict:
    """Call Groq vision model and parse response as JSON."""
    json_prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no markdown formatting."

    raw = vision_completion(
        image_data_url=image_data_url,
        prompt=json_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        return json.loads(raw)


# ---------------------------------------------------------------------------
# Embeddings (ChromaDB built-in — local, free, no API needed)
# ---------------------------------------------------------------------------

def get_embeddings(texts: list[str], model: str | None = None) -> list[list[float]]:
    """
    Get embeddings using ChromaDB's built-in embedding function.
    Uses all-MiniLM-L6-v2 via ONNX Runtime — runs locally, no API key needed.
    """
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        logger.info("Loading ChromaDB default embedding model (all-MiniLM-L6-v2 via ONNX)")
        _embedding_fn = DefaultEmbeddingFunction()
    return _embedding_fn(texts)
