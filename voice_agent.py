import logging
import os
from typing import Final

import requests

VOICE_STAGE_ORDER: Final[dict[str, str]] = {
    "intro": "qualification",
    "qualification": "closing",
    "closing": "closing",
}

GEMINI_API_URL: Final[str] = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_GEMINI_MODEL: Final[str] = "gemini-2.5-flash-lite"

logger = logging.getLogger(__name__)


def get_next_stage(stage: str) -> str:
    return VOICE_STAGE_ORDER.get(stage, "closing")


def build_voice_prompt(stage: str, message: str) -> str:
    return f"""You are a human-like outbound sales agent.

Stage: {stage}

Rules:
- Be concise
- Ask ONLY one question at a time
- Sound natural and conversational
- Guide user toward interest

Flow:
- intro: greet and ask interest
- qualification: ask needs/budget
- closing: suggest next step

User: {message}
"""


def extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""

    parts = (((candidates[0] or {}).get("content") or {}).get("parts")) or []
    texts = [part.get("text", "").strip() for part in parts if part.get("text")]
    return " ".join(texts).strip()


def call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    response = requests.post(
        GEMINI_API_URL.format(model=model),
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 160,
            },
        },
        timeout=30,
    )

    if not response.ok:
        logger.warning("Gemini request failed: %s %s", response.status_code, response.text)
        raise RuntimeError("Gemini API request failed.")

    reply = extract_gemini_text(response.json())
    if not reply:
        raise RuntimeError("Gemini returned an empty response.")

    return reply


def build_voice_fallback(stage: str) -> str:
    if stage == "intro":
        return "Thanks for picking up. Would you like to hear how our AI service can help your team?"
    if stage == "qualification":
        return "What kind of problem are you hoping to solve, and do you already have a budget in mind?"
    return "It sounds promising. Would you be open to a short demo or follow-up conversation next?"
