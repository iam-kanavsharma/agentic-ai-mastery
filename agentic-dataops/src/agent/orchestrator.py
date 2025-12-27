# add/ensure these
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .core import dq_check, ensure_dir, load_df, profile_df, save_df, transform
from .memory import MEM, safe_path, save_memory


def write_report(title: str, sections: List[Tuple[str, str]], out_dir: Optional[str] = None) -> str:
    rpt_dir = out_dir or MEM["preferences"]["report_dir"]
    rpt_dir = safe_path(rpt_dir)
    ensure_dir(rpt_dir)
    name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title.replace(' ','_')}.md"
    path = os.path.join(rpt_dir, name)
    content = [f"# {title}", ""]
    for h, body in sections:
        content.append(f"## {h}\n\n{body}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    return path

# ---------- Planner ----------
def plan(goal: str, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = []
    sales = inputs.get("sales_path")
    regions = inputs.get("regions_path")
    out_path = inputs.get("out_path")
    rules = inputs.get("dq_rules", {})
    recipe = inputs.get("recipe", {})
    title = inputs.get("report_title", "DataOps Agent Run")

    steps.append({"op": "load_sales", "path": sales})
    if regions:
        steps.append({"op": "load_regions", "path": regions})
    steps.append({"op": "profile_input"})
    if recipe:
        steps.append({"op": "transform", "recipe": recipe})
    if rules:
        steps.append({"op": "dq_check", "rules": rules})
    if out_path:
        steps.append({"op": "save", "path": out_path})
    steps.append({"op": "profile_output"})
    steps.append({"op": "report", "title": title})
    return steps

# ---------- Reflection ----------
def reflect(run_log: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues = []
    dq_req = run_log.get("dq_requested", False)
    if dq_req and not run_log.get("dq_ok", False):
        issues.append("DQ checks failed.")
    if run_log.get("saved", False) and run_log.get("output_profile", {}).get("rows", 0) == 0:
        issues.append("Output has zero rows.")
    return (len(issues) == 0, issues)

# ---------- Orchestrator ----------
def run_agent(goal: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    steps = plan(goal, inputs)
    log: Dict[str, Any] = {
        "goal": goal,
        "steps": steps,
        "dq_requested": "dq_rules" in inputs and bool(inputs["dq_rules"]),
        "sections": []
    }

    sales_df = None
    regions_df = None
    output_df = None

    for st in steps:
        op = st["op"]

        if op == "load_sales":
            sales_df = load_df(st["path"])
            log["sales_path"] = st["path"]
            log["sections"].append(("Loaded Sales", f"Rows: {len(sales_df)}  |  Path: {st['path']}"))

        elif op == "load_regions":
            regions_df = load_df(st["path"])
            log["regions_path"] = st["path"]
            log["sections"].append(("Loaded Regions", f"Rows: {len(regions_df)}  |  Path: {st['path']}"))

        elif op == "profile_input":
            prof = profile_df(sales_df)
            log["input_profile"] = prof
            log["sections"].append(("Input Profile", json.dumps(prof, indent=2)))

        elif op == "transform":
            aux = {}
            if regions_df is not None:
                aux["regions"] = regions_df
            output_df = transform(sales_df, st["recipe"], aux)
            log["transform_recipe"] = st["recipe"]
            log["sections"].append(("Transform", "Applied recipe successfully."))

        elif op == "dq_check":
            df = output_df if output_df is not None else sales_df
            ok, issues = dq_check(df, st["rules"])
            log["dq_ok"] = ok
            log["dq_issues"] = issues
            log["sections"].append(("Data Quality", "OK" if ok else "Issues:\n- " + "\n- ".join(issues)))

        elif op == "save":
            df = output_df if output_df is not None else sales_df
            save_df(df, st["path"])
            log["saved"] = True
            log["out_path"] = st["path"]
            log["sections"].append(("Save", f"Saved to {st['path']}"))

        elif op == "profile_output":
            df = output_df if output_df is not None else sales_df
            prof = profile_df(df)
            log["output_profile"] = prof
            log["sections"].append(("Output Profile", json.dumps(prof, indent=2)))

        elif op == "report":
            ok, issues = reflect(log)
            log["reflection_ok"] = ok
            log["reflection_issues"] = issues
            body_issues = "None" if ok else "\n- " + "\n- ".join(issues)
            log["sections"].append(("Reflection", f"Pass: {ok}\nIssues: {body_issues}"))
            rpt_path = write_report(st["title"], log["sections"], MEM["preferences"]["report_dir"])
            log["report_path"] = rpt_path

    # persist run summary
    MEM["runs"].append({
        "timestamp": datetime.now().isoformat(),
        "goal": goal,
        "out_path": log.get("out_path"),
        "report_path": log.get("report_path"),
        "reflection_ok": log.get("reflection_ok", False)
    })
    save_memory(MEM)

    return log
