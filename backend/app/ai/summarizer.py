"""Complaint summarization using Gemini or OpenAI."""

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


async def summarize_complaint(text: str, max_length: int = 150) -> str:
    settings = get_settings()

    if len(text.split()) <= 30:
        return text[:max_length]

    try:
        if settings.AI_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            return await _summarize_gemini(text, max_length)
        elif settings.OPENAI_API_KEY:
            return await _summarize_openai(text, max_length)
    except Exception as e:
        logger.warning("AI summarization failed, using truncation: %s", e)

    return text[:max_length] + "..."


async def _summarize_gemini(text: str, max_length: int) -> str:
    import google.generativeai as genai

    genai.configure(api_key=get_settings().GEMINI_API_KEY)
    settings = get_settings()
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    prompt = f"Summarize this civic complaint in one concise sentence (max {max_length} chars):\n\n{text}"
    response = model.generate_content(prompt)
    return response.text.strip()[:max_length]


async def _summarize_openai(text: str, max_length: int) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=get_settings().OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize civic complaints concisely in one sentence."},
            {"role": "user", "content": text},
        ],
        max_tokens=60,
    )
    return response.choices[0].message.content.strip()[:max_length]
