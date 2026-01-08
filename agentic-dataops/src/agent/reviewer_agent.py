import json
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .llm_client import LLMClient

@dataclass
class ReviewResult:
    approved: bool
    feedback: str

REVIEWER_SYSTEM_PROMPT = """
You are a Senior Data Engineer reviewing a DataOps recipe. 
The recipe is a JSON object defining data transformations (Pandas/Spark).

Your Goal: Ensure the recipe is logically correct, efficient, and secure.

Rules:
1. logical_correctness: Does the recipe actually answer the User's Prompt?
2. efficiency: Are there obvious issues (e.g. Cartesian joins)?
3. security: Are there suspicious patterns?

Return a JSON object with:
{
    "approved": boolean,
    "feedback": "string explaining reasoning"
}
"""

class ReviewerAgent:
    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()

    def review_recipe(self, user_prompt: str, recipe: Dict[str, Any], context: str = "") -> ReviewResult:
        """
        Reviews a generated recipe against the user prompt.
        """
        full_prompt = (
            f"{REVIEWER_SYSTEM_PROMPT}\n\n"
            f"User Prompt: {user_prompt}\n"
            f"Context: {context}\n"
            f"Generated Recipe: {json.dumps(recipe, indent=2)}\n\n"
            "Review Decision JSON:"
        )
        
        try:
            raw_response = self.llm.generate(full_prompt, temperature=0.0)
            # Defensive JSON parsing
            clean_json = self._extract_json(raw_response)
            data = json.loads(clean_json)
            
            return ReviewResult(
                approved=data.get("approved", False),
                feedback=data.get("feedback", "No feedback provided.")
            )
        except Exception as e:
            # Fail safe: unparseable review means we shouldn't run it blindly
            return ReviewResult(approved=False, feedback=f"Reviewer Error: {str(e)}")

    def _extract_json(self, text: str) -> str:
        s = text.strip()
        first = s.find("{")
        last = s.rfind("}")
        if first == -1 or last == -1:
            return text # Let json.loads fail naturally
        return s[first : last + 1]
