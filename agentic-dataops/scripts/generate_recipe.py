"""Example script: generate a recipe from a natural language prompt using OpenAI.

Usage:
  python scripts/generate_recipe.py "Create daily revenue by region"
  python scripts/generate_recipe.py "..." --out recipes/generated.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent import orchestrator
from agent.agent_recipe_generator import generate_recipe_from_prompt
from agent.llm_client import LLMClient
from dotenv import load_dotenv

# Load environment variables from agentic-dataops/.env so the script works
# both inside VS Code (python.envFile) and when run from the CLI.
load_dotenv(dotenv_path=Path(__file__).parents[1] / ".env")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("prompt", help="Natural language description of desired recipe")
    p.add_argument("--out", help="Write generated recipe to this file (JSON)")
    # Leave `--model` empty to prefer env-configured Vertex/Gemini model (VERTEX_MODEL).
    p.add_argument("--model", default=None, help="Model id to use (leave empty to use VERTEX_MODEL or OPENAI_MODEL env)")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--run", action="store_true", help="Immediately run the generated recipe via the orchestrator (requires --sales-path and --out-path)")
    p.add_argument("--sales-path", help="Path to sales CSV (required with --run)")
    p.add_argument("--regions-path", help="Path to regions CSV (optional for --run)")
    p.add_argument("--out-path", help="Path to save cleaned output (required with --run)")
    p.add_argument("--report-title", default="Generated Run", help="Report title when running the recipe")
    p.add_argument("--mock", action="store_true", help="Use a canned recipe (no LLM call) for testing/demo")
    args = p.parse_args()

    if args.mock:
      # simple canned recipe useful for demos/tests
      recipe = {
        "select": ["order_id", "date", "region", "revenue", "product_id"],
        "filter": "region in ['APAC','EMEA','AMER'] and revenue >= 0",
        "derive": [
          {"name": "date_day", "expr": "pd.to_datetime(df['date']).dt.date.astype(str)"},
          {"name": "rev_in_k", "expr": "df['revenue'] / 1000"}
        ],
        "join": {"right_df": "regions", "on": ["region"], "how": "left"},
        "groupby": {"by": ["date_day","region","region_name"], "agg": {"revenue":"sum"}}
      }
    else:
      llm = LLMClient(model=args.model)
      recipe = generate_recipe_from_prompt(args.prompt, llm, temperature=args.temperature)

    print(json.dumps(recipe, indent=2))

    if args.out:
      outp = Path(args.out)
      outp.parent.mkdir(parents=True, exist_ok=True)
      outp.write_text(json.dumps(recipe, indent=2))
      print(f"Wrote recipe to {outp}")

    if args.run:
      # require paths
      if not args.sales_path or not args.out_path:
        raise SystemExit("--run requires --sales-path and --out-path")
      inputs = {
        "sales_path": args.sales_path,
        "regions_path": args.regions_path,
        "recipe": recipe,
        "out_path": args.out_path,
        "dq_rules": {},
        "report_title": args.report_title,
      }
      print("Running orchestrator with generated recipe...")
      result = orchestrator.run_agent(args.report_title, inputs)
      print("Run finished. Report:", result.get("report_path"))
      if result.get("out_path"):
        print("Saved output:", result.get("out_path"))


if __name__ == "__main__":
    main()
