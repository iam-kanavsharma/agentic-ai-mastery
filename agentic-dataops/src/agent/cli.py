# cli.py
from __future__ import annotations

import json
import os
import traceback
from typing import Any, Dict, Optional

import typer
from agent.core import list_datasets
from agent.memory import MEM, SAFE_ROOT, safe_path
from agent.orchestrator import run_agent

app = typer.Typer(no_args_is_help=True)

import subprocess
import sys


@app.command()
def test(
    k: str = typer.Option(None, "--k", help="Only run tests matching expression (pytest -k)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output."),
    cov: bool = typer.Option(False, "--cov", help="Run coverage if coverage/pytest-cov installed."),
):
    """
    Run the project's pytest suite.
    """
    try:
        # Ensure src/ is on sys.path for imports
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [os.path.abspath("src"), env.get("PYTHONPATH", "")]
        )

        cmd = [sys.executable, "-m", "pytest", "tests"]
        if k:
            cmd += ["-k", k]
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        if cov:
            # Runs `pytest --cov=agent --cov-report=term-missing`
            cmd += ["--cov=agent", "--cov-report=term-missing"]

        typer.echo(f"Running: {' '.join(cmd)}")
        rc = subprocess.call(cmd, env=env)
        if rc != 0:
            raise typer.Exit(code=rc)
    except FileNotFoundError:
        typer.secho("pytest is not installed in this environment.", fg=typer.colors.RED)
        typer.echo("Install via: pip install -e .   (pyproject includes pytest)")
        sys.exit(rc)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        sys.exit(rc)

# --- Helpers -----------------------------------------------------------------
def _load_structured_file(path: Optional[str]) -> Dict[str, Any]:
    """Load JSON or YAML file if provided; return {} if None."""
    if not path:
        return {}
    full = safe_path(path)
    if not os.path.exists(full):
        raise typer.BadParameter(f"File not found: {path}")
    ext = os.path.splitext(full)[1].lower()
    with open(full, "r", encoding="utf-8") as f:
        text = f.read()
    if ext in (".json",):
        return json.loads(text)
    elif ext in (".yml", ".yaml"):
        try:
            import yaml  # type: ignore
        except Exception:
            raise typer.BadParameter(
                "YAML file provided but PyYAML is not installed. "
                "Install with: pip install pyyaml"
            )
        return yaml.safe_load(text) or {}
    else:
        raise typer.BadParameter("Only .json, .yml, .yaml supported for recipe/rules.")


def _echo_json(obj: Any):
    typer.echo(json.dumps(obj, indent=2))


# --- Commands ----------------------------------------------------------------
@app.command()
def list(
    base_dir: Optional[str] = typer.Option(
        None, "--base-dir", help="Base directory to scan for datasets."
    )
):
    """
    List available datasets (.csv / .parquet) under base_dir (default from memory).
    """
    try:
        items = list_datasets(base_dir)
        _echo_json({"base_dir": base_dir or MEM["preferences"]["base_dir"], "datasets": items})
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def run(
    goal: str = typer.Argument(..., help="High-level goal for the agent run."),
    sales_path: str = typer.Option(..., "--sales-path", help="Path to sales dataset."),
    regions_path: Optional[str] = typer.Option(
        None, "--regions-path", help="Optional path to regions dataset."
    ),
    out_path: Optional[str] = typer.Option(
        None, "--out-path", help="Output file path (.csv or .parquet)."
    ),
    recipe: Optional[str] = typer.Option(
        None, "--recipe", help="Transform recipe file (.json/.yml/.yaml)."
    ),
    dq_rules: Optional[str] = typer.Option(
        None, "--dq-rules", help="DQ rules file (.json/.yml/.yaml)."
    ),
    report_title: Optional[str] = typer.Option(
        None, "--report-title", help="Title for the generated Markdown report."
    ),
):
    """
    Execute the DataOps pipeline with optional recipe and DQ rules.
    """
    try:
        # Safe path validations
        sales_path = os.path.relpath(safe_path(sales_path), SAFE_ROOT)
        regions_path_rel = (
            os.path.relpath(safe_path(regions_path), SAFE_ROOT) if regions_path else None
        )
        out_path_rel = os.path.relpath(safe_path(out_path), SAFE_ROOT) if out_path else None

        # Load recipe and rules (files optional)
        recipe_obj = _load_structured_file(recipe)
        dq_obj = _load_structured_file(dq_rules)

        inputs: Dict[str, Any] = {
            "sales_path": sales_path,
            "regions_path": regions_path_rel,
            "recipe": recipe_obj,
            "dq_rules": dq_obj,
            "out_path": out_path_rel,
            "report_title": report_title or "DataOps Agent Run",
        }

        result = run_agent(goal, inputs)

        # Return concise run summary
        _echo_json(
            {
                "goal": goal,
                "sales_path": sales_path,
                "regions_path": regions_path_rel,
                "out_path": result.get("out_path"),
                "report_path": result.get("report_path"),
                "reflection_ok": result.get("reflection_ok"),
                "dq_ok": result.get("dq_ok"),
                "dq_issues": result.get("dq_issues", []),
            }
        )
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command()
def history(limit: int = typer.Option(10, "--limit", min=1, help="Number of recent runs.")):
    """
    Show recent runs persisted in agent_memory.json.
    """
    try:
        runs = MEM.get("runs", [])
        if limit:
            runs = runs[-limit:]
        _echo_json({"count": len(runs), "runs": runs})
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        traceback.print_exc()
        raise typer.Exit(code=1)


# --- Entrypoint ---------------------------------------------------------------
def main():
    app()


if __name__ == "__main__":
    main()
