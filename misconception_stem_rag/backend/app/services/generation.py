"""Service helpers for question generation via OpenAI."""

from __future__ import annotations

import json
from typing import Any, Mapping
from textwrap import dedent

from openai import OpenAI

from ..config import get_settings

_settings = get_settings()
_client: OpenAI | None = None


def _build_prompt(fact_context: str, misconceptions: list[str], traits: Mapping[str, Any]) -> str:
    formatted_misconceptions = (
        "\n".join(f"- {item}" for item in misconceptions) if misconceptions else "- None supplied"
    )
    trait_lines = (
        "\n".join(f"- {name}: {value}" for name, value in traits.items()) if traits else "- baseline"
    )
    return dedent(
        f"""
        ### Factual Source Material
        {fact_context.strip() or "No factual context provided."}

        ### Misconceptions to Challenge
        {formatted_misconceptions}

        ### Learner Cognitive Profile
        {trait_lines}

        ### Authoring Brief
        1. Craft one advanced STEM multiple-choice question that exposes the listed misconceptions while remaining anchored to the factual source.
        2. Calibrate phrasing, rigor, and distractor subtlety in response to the learner profile. Lower confidence values should gently scaffold; higher analytical depth should invite multi-step reasoning.
        3. Produce exactly four options: one correct, one misconception-aligned, one partial-understanding, and one procedural error. Each option must carry the matching `type` label.
        4. Provide a concise rationale in the `explanation` clarifying why the correct option is right and how the misconception distractor fails.
        5. Select `difficulty` from ["easy", "medium", "hard"].

        ### JSON Response Schema
        {{
          "stem": "...",
          "options": [
            {{"text": "...", "type": "correct"}},
            {{"text": "...", "type": "misconception"}},
            {{"text": "...", "type": "partial"}},
            {{"text": "...", "type": "procedural"}}
          ],
          "explanation": "...",
          "difficulty": "easy|medium|hard"
        }}

        Return only a JSON object matching the schema with no commentary or code fences.
        """
    )


def _fallback_question() -> dict[str, Any]:
    return {
        "stem": "What is the acceleration due to gravity on Earth near the surface?",
        "options": [
            {"text": "Approximately 9.8 m/s^2 downward", "type": "correct"},
            {"text": "Approximately 9.8 m/s upward", "type": "misconception"},
            {"text": "Approximately 9.8 m/s^2 sideways", "type": "partial"},
            {"text": "Zero when an object is stationary", "type": "procedural"},
        ],
        "explanation": "Gravity accelerates objects toward Earth's center at about 9.8 m/s^2.",
        "difficulty": "easy",
    }


def _get_client() -> OpenAI | None:
    global _client  # noqa: PLW0603 - module level singleton
    api_key = _settings.openai_api_key
    if not api_key or "REDACTED" in api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def _parse_response(payload: str | dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any]
    if isinstance(payload, dict):
        data = payload
    else:
        data = json.loads(payload)

    required_fields = {"stem", "options", "explanation", "difficulty"}
    missing = required_fields - set(data.keys())
    if missing:
        raise ValueError(f"Missing keys in model response: {', '.join(sorted(missing))}")

    options = data.get("options", [])
    if not isinstance(options, list) or not options:
        raise ValueError("Options list is empty or invalid")

    normalized: list[dict[str, Any]] = []
    for option in options:
        if not isinstance(option, dict) or "text" not in option or "type" not in option:
            raise ValueError("Each option must include 'text' and 'type'")
        normalized.append({"text": str(option["text"]), "type": str(option["type"])})

    data["stem"] = str(data["stem"])
    data["explanation"] = str(data["explanation"])
    data["difficulty"] = str(data["difficulty"]).lower()
    data["options"] = normalized
    return data


def generate_question(
    fact_context: str,
    misconceptions: list[str],
    traits: Mapping[str, Any],
) -> dict[str, Any]:
    """Generate a question using OpenAI with fallbacks for reliability."""

    prompt = _build_prompt(fact_context, misconceptions, traits)
    client = _get_client()

    if client is None:
        return _fallback_question()

    try:
        model_name = _settings.openai_model or "gpt-4o-mini"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert STEM assessment designer. You must return a single JSON object that "
                    "strictly follows the provided schema. Never include explanations, prose, or markdown fences."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.35,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty model response")
        return _parse_response(content)
    except Exception:
        # Retry once before returning fallback
        try:
            response = client.chat.completions.create(
                model=_settings.openai_model or "gpt-4o-mini",
                messages=messages,
                temperature=0.45,
            )
            content = response.choices[0].message.content
            if content:
                return _parse_response(content)
        except Exception:
            pass
        return _fallback_question()
