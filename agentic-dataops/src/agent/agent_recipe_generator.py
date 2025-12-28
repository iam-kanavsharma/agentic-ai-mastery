"""Generate validated recipe dicts from a natural-language prompt via LLM.

This module provides a small helper that asks an LLM to return a JSON-only
recipe matching the repo's expected recipe schema. The output is parsed and
validated minimally before being returned.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from .llm_client import LLMClient

DEFAULT_PROMPT_TEMPLATE = (
    "Given the user request, produce a JSON object that represents a recipe\n"
    "for the agentic-dataops project. The JSON must contain only the keys\n"
    "used by `transform()`: optional `select` (list), optional `filter` (string),\n"
    "optional `derive` (list of {name, expr}), optional `join` (object),\n"
    "and optional `groupby` (object). Return ONLY valid JSON (no surrounding\n"
    "markdown). Example: {\n"
    "  \"select\": [\"order_id\", \"date\"],\n"
    "  \"derive\": [{\"name\":\"date_day\", \"expr\":\"pd.to_datetime(df['date']).dt.date.astype(str)\"}]\n"
    "}\n"
)


def generate_recipe_from_prompt(prompt: str, llm: LLMClient, temperature: float = 0.0) -> Dict[str, Any]:
    """Generate a recipe dict from a natural-language prompt using `llm`.

    This performs minimal validation and returns a dict suitable for
    `transform()`.
    """
    full_prompt = DEFAULT_PROMPT_TEMPLATE + "\nUser request: " + prompt
    raw = llm.generate(full_prompt, temperature=temperature)

    # Try to extract JSON from the response (defensive)
    # Find first { and last } to get a JSON blob
    s = raw.strip()
    first = s.find("{")
    last = s.rfind("}")
    if first == -1 or last == -1:
        raise ValueError("LLM did not return a JSON object for the recipe")
    blob = s[first : last + 1]

    try:
        obj = json.loads(blob)
    except json.JSONDecodeError as e:
        raise ValueError("Failed to parse JSON from LLM response") from e

    # Minimal validation: ensure types match expected simple schema
    if "select" in obj and not isinstance(obj["select"], list):
        raise ValueError("`select` must be a list")
    if "derive" in obj:
        if not isinstance(obj["derive"], list):
            raise ValueError("`derive` must be a list of {name, expr}")
        for d in obj["derive"]:
            if not isinstance(d, dict) or "name" not in d or "expr" not in d:
                raise ValueError("Each derive item must be an object with 'name' and 'expr'")

    return obj


__all__ = ["generate_recipe_from_prompt"]
