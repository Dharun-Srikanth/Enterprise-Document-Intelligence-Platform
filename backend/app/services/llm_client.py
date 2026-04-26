"""OpenAI LLM client wrapper with retry logic."""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_client = None


def get_openai_client():
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        from openai import OpenAI
        from app.config import get_settings
        settings = get_settings()
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        if not api_key or api_key == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY not set. Please set it in .env file.")
        _client = OpenAI(api_key=api_key)
    return _client


def chat_completion(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None,
    max_retries: int = 3,
) -> str:
    """
    Call OpenAI chat completion with retry logic.

    Returns the assistant message content as string.
    """
    client = get_openai_client()

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
            logger.warning(f"OpenAI API attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                raise
            import time
            time.sleep(2 ** attempt)  # Exponential backoff

    return ""


def chat_completion_json(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    max_retries: int = 3,
) -> dict:
    """Call OpenAI and parse response as JSON."""
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
        # Try to extract JSON from markdown code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        return json.loads(raw)


def vision_completion(
    image_data_url: str,
    prompt: str,
    model: str = "gpt-4o",
    temperature: float = 0.1,
    max_tokens: int = 1500,
    max_retries: int = 3,
) -> str:
    """Call OpenAI vision model with an image."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url, "detail": "high"},
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
    model: str = "gpt-4o",
    temperature: float = 0.1,
    max_tokens: int = 1500,
    max_retries: int = 3,
) -> dict:
    """Call OpenAI vision model and parse response as JSON."""
    raw = vision_completion(
        image_data_url=image_data_url,
        prompt=prompt,
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


def get_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """Get embeddings for a list of texts."""
    client = get_openai_client()
    response = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in response.data]
