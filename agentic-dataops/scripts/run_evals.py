import json
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load env vars first
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Set default backend to vertex if not specified
if "LLM_BACKEND" not in os.environ:
    os.environ["LLM_BACKEND"] = "vertex"

from agent.agent_recipe_generator import generate_recipe_from_prompt
from agent.llm_client import LLMClient
from agent.reviewer_agent import ReviewerAgent

def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evals():
    dataset_path = os.path.join("tests", "evals", "golden_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        return

    dataset = load_dataset(dataset_path)
    llm = LLMClient()
    
    passed = 0
    total = len(dataset)
    
    print(f"=== Running Evals on {total} cases ===")
    
    for case in dataset:
        print(f"\nProcessing case: {case['id']}")
        print(f"  Prompt: {case['prompt']}")
        
        try:
            # Mock context to match what the real app provides
            mock_context = (
                "- sales: ['order_id', 'date', 'region', 'revenue', 'product_id']\n"
                "- regions: ['region', 'region_name']"
            )
            result = generate_recipe_from_prompt(case["prompt"], llm, dataset_context=mock_context)
            
            # Check Clarification
            if case.get("expected_clarification"):
                if "clarification" in result:
                    print("  [PASS] Correctly asked for clarification.")
                    passed += 1
                else:
                    print(f"  [FAIL] Expected clarification, but got recipe: {result.keys()}")
                continue

            # Run Reviewer
            reviewer = ReviewerAgent(llm=llm)
            review = reviewer.review_recipe(case["prompt"], result, context=mock_context)
            if not review.approved:
                print(f"  [FAIL] Reviewer rejected valid recipe: {review.feedback}")
                continue
            
            # Check Keys
            if "clarification" in result:
                 print(f"  [FAIL] Unexpected clarification: {result['clarification']}")
                 continue

            missing_keys = [k for k in case.get("expected_keys", []) if k not in result]
            forbidden_present = [k for k in case.get("forbidden_keys", []) if k in result]
            
            if missing_keys:
                print(f"  [FAIL] Missing keys: {missing_keys}")
                print(f"  [DEBUG] LLM Output: {result}")
                break
            elif forbidden_present:
                print(f"  [FAIL] Forbidden keys present: {forbidden_present}")
                break
            else:
                print("  [PASS] Schema validation successful.")
                passed += 1
                
        except Exception as e:
            print(f"  [Error] Exception during generation: {e}")

    print(f"\n=== Summary: {passed}/{total} Passed ({passed/total*100:.1f}%) ===")

if __name__ == "__main__":
    run_evals()
