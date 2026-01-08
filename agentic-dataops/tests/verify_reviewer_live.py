import sys
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Ensure LLM backend is set
if "LLM_BACKEND" not in os.environ:
    os.environ["LLM_BACKEND"] = "vertex"

from agent.reviewer_agent import ReviewerAgent

def verify_live():
    print("=== Review Agent Live Verification ===")
    agent = ReviewerAgent()

    # Case 1: Good Recipe
    print("\n1. Testing GOOD Recipe...")
    prompt_good = "Calculate total revenue by region"
    recipe_good = {
        "select": ["region", "revenue"],
        "groupby": {"by": ["region"], "agg": {"revenue": "sum"}}
    }
    result = agent.review_recipe(prompt_good, recipe_good, context="- sales: ['region', 'revenue']")
    print(f"Approved: {result.approved}")
    print(f"Feedback: {result.feedback}")
    if not result.approved:
        print("[FAIL] Expected approval for good recipe.")

    # Case 2: Bad Recipe (Logic mismatch)
    print("\n2. Testing BAD Recipe (Logic Mismatch)...")
    prompt_bad = "Calculate total revenue by region"
    recipe_bad = {
        "select": ["product_id"], # Irrelevant column
        "filter": "revenue > 1000" # Not answering the prompt
    }
    result = agent.review_recipe(prompt_bad, recipe_bad, context="- sales: ['region', 'revenue']")
    print(f"Approved: {result.approved}")
    print(f"Feedback: {result.feedback}")
    if result.approved:
        print("[FAIL] Expected rejection for bad recipe.")

if __name__ == "__main__":
    verify_live()
