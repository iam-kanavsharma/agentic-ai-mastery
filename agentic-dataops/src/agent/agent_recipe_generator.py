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
    "markdown). \n"
    "If the user request is vague, nonsense, or not related to data operations,\n"
    "return a JSON with a single key `clarification` containing a question string.\n"
    "Example Recipe: {\n"
    "  \"select\": [\"order_id\", \"date\", \"region\"],\n"
    "  \"join\": {\"right_df\": \"regions\", \"on\": [\"region\"], \"how\": \"left\"},\n"
    "  \"derive\": [{\"name\":\"date_day\", \"expr\":\"pd.to_datetime(df['date']).dt.date.astype(str)\"}],\n"
    "  \"groupby\": {\"by\": [\"date_day\", \"region_name\"], \"agg\": {\"revenue\": \"sum\"}}\n"
    "}\n"
    "Example Clarification: {\n"
    "  \"clarification\": \"Could you specify which dataset you want to analyze?\"\n"
    "}\n"
)



PYSPARK_INSTRUCTIONS = (
    "\nIMPORTANT: The user wants a PySpark recipe. \n"
    "For `derive` expressions, usage PySpark `pyspark.sql.functions` syntax.\n"
    "Example Derive: [{\"name\": \"year\", \"expr\": \"year(col('date'))\"}]\n"
    "Do NOT use Pandas syntax like `df['col']`."
)

def generate_recipe_from_prompt(prompt: str, llm: LLMClient, temperature: float = 0.0, dataset_context: str = "", dialect: str = "pandas") -> Dict[str, Any]:
    """Generate a recipe dict from a natural-language prompt using `llm`.

    Args:
        dialect: 'pandas' or 'pyspark'. Controls the syntax advice given to the LLM.
    """
    full_prompt = DEFAULT_PROMPT_TEMPLATE
    
    if dialect == "pyspark":
        full_prompt += PYSPARK_INSTRUCTIONS
        
    if dataset_context:
        full_prompt += f"\nContext - Available Datasets:\n{dataset_context}\n"
    
    full_prompt += "\nUser request: " + prompt
    print(full_prompt)
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

    # Check for clarification request
    if "clarification" in obj:
        return obj  # Return the clarification object directly

    # Minimal validation: ensure types match expected simple schema
    if "select" in obj and not isinstance(obj["select"], list):
        raise ValueError("`select` must be a list")
    if "derive" in obj:
        if not isinstance(obj["derive"], list):
            raise ValueError("`derive` must be a list of {name, expr}")
        for d in obj["derive"]:
            if not isinstance(d, dict) or "name" not in d or "expr" not in d:
                raise ValueError("Each derive item must be an object with 'name' and 'expr'")
    if "groupby" in obj:
        if "by" not in obj["groupby"]:
            raise ValueError("`groupby` must contain a 'by' key")
    if "join" in obj:
        if "right_df" not in obj["join"]:
            raise ValueError("`join` must contain a 'right_df' key")
        if "on" not in obj["join"]:
            raise ValueError("`join` must contain an 'on' key")

    return obj


__all__ = ["generate_recipe_from_prompt"]
