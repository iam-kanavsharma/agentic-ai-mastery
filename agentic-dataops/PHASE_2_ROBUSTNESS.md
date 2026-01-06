# Phase 2: Robustness & Evaluations

This phase prioritized evolving the agent from a simple "happy path" executor into a robust system capable of self-evaluation and handling ambiguity. The primary goal was ensuring the agent only executes data operations when it clearly understands the user's intent.

## 1. The Robustness Problem
Previously, the agent attempted to generate a recipe for *any* prompt, including nonsense like *"I do not know what I am talking about"*. This occurred because the system prompt forced the LLM to return a JSON recipe structure regardless of the input's semantic validity.

### The Fix: Clarification Loop
The logic in `src/agent/agent_recipe_generator.py` was updated to allow the LLM to opt-out of recipe generation.

**Before:**
The agent would hallucinate column names and operations to satisfy the JSON requirement, often leading to runtime errors or meaningless results.

**After:**
The agent now recognizes vague or irrelevant prompts and returns a specific clarification signal.
> **Agent Response:** "CLARIFICATION NEEDED: Could you please describe the data analysis or transformation you would like to perform on the sales or regions datasets?"

This was achieved by injecting instructions into the system prompt that permit the LLM to return a `{"clarification": "..."}` object instead of a recipe.

## 2. Quantitative Evaluation (Evals)
To ensure these improvements (and future changes) don't regress, the project moved away from manual "vibes-based" testing to a systematic evaluation framework.

### The Golden Dataset
A "Golden Dataset" was established in `tests/evals/golden_dataset.json` to define ground truth behavior. This dataset includes:
1.  **Valid Cases**: Prompts like *"Calculate total revenue by region name"* where specific operations (`groupby`, `join`) are expected.
2.  **Invalid Cases**: Prompts like *"blue horses flying underwater"* where a clarification request is strictly expected.

### The Eval Runner
A script, `scripts/run_evals.py`, was built to run these cases against the live agent code. This script:
-   Iterates through the dataset.
-   Calls the internal generator logic.
-   Validates the output against expected keys or clarification states.
-   Provides a pass/fail summary.

**Current Results:**
The agent currently scores **100% (3/3)** on the baseline dataset, confirming that the clarification loop works as intended without breaking normal functionality.

## Next Steps
With a robust foundation and a way to measure accuracy, the roadmap points toward **Multi-Agent Patterns**, specifically adding a "Reviewer" agent to critique complex recipes before execution.
