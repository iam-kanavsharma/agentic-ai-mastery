
# agent_dataops_poc.py
import os, json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

# ---------- Config & Memory ----------
MEMORY_FILE = "agent_memory.json"

def load_memory() -> Dict[str, Any]:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "preferences": {
            "base_dir": "data",
            "output_dir": "clean",
            "report_dir": "reports",
            "default_format": "parquet"
        },
        "runs": []
    }

def save_memory(mem: Dict[str, Any]):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)

MEM = load_memory()
SAFE_ROOT = os.getcwd()

def _safe_path(*parts) -> str:
    path = os.path.abspath(os.path.join(*parts))
    if not path.startswith(SAFE_ROOT):
        raise ValueError("Access outside working directory is not allowed.")
    return path

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

# ---------- Tools ----------
def list_datasets(base_dir: Optional[str] = None) -> List[str]:
    base = base_dir or MEM["preferences"]["base_dir"]
    base = _safe_path(base)
    ensure_dir(base)
    items = []
    for root, _, files in os.walk(base):
        for fn in files:
            if fn.lower().endswith((".csv", ".parquet")):
                items.append(os.path.relpath(os.path.join(root, fn), SAFE_ROOT))
    return sorted(items)

def load_df(path: str) -> pd.DataFrame:
    full = _safe_path(path)
    if path.lower().endswith(".csv"):
        return pd.read_csv(full)
    if path.lower().endswith(".parquet"):
        return pd.read_parquet(full)
    raise ValueError("Unsupported file type. Use .csv or .parquet")

def save_df(df: pd.DataFrame, out_path: str):
    full = _safe_path(out_path)
    ensure_dir(os.path.dirname(full))
    if out_path.lower().endswith(".csv"):
        df.to_csv(full, index=False)
    elif out_path.lower().endswith(".parquet"):
        df.to_parquet(full, index=False)
    else:
        raise ValueError("Unsupported output type. Use .csv or .parquet")

def profile_df(df: pd.DataFrame, max_cats: int = 10) -> Dict[str, Any]:
    prof = {"rows": int(len(df)), "cols": int(df.shape[1]), "columns": {}}
    for col in df.columns:
        s = df[col]
        info = {
            "dtype": str(s.dtype),
            "nulls": int(s.isna().sum()),
            "null_pct": float((s.isna().mean() * 100)),
            "nunique": int(s.nunique(dropna=True))
        }
        if pd.api.types.is_numeric_dtype(s):
            desc = s.describe()
            info.update({
                "min": None if pd.isna(desc.get("min")) else float(desc["min"]),
                "max": None if pd.isna(desc.get("max")) else float(desc["max"]),
                "mean": None if pd.isna(desc.get("mean")) else float(desc["mean"]),
                "std": None if pd.isna(desc.get("std")) else float(desc["std"]),
            })
        else:
            vc = s.value_counts(dropna=True).head(max_cats)
            info["top_values"] = vc.to_dict()
        prof["columns"][col] = info
    return prof

def dq_check(df: pd.DataFrame, rules: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Rules example:
    {
      "non_null": ["order_id", "revenue"],
      "unique": ["order_id"],
      "range": {"revenue": {"min": 0}},
      "allowed_values": {"region": ["APAC","EMEA","AMER"]}
    }
    """
    issues = []
    for col in rules.get("non_null", []):
        if col not in df.columns:
            issues.append(f"Column missing for non_null: {col}")
        else:
            n = int(df[col].isna().sum())
            if n > 0:
                issues.append(f"Non-null violation: {col} has {n} nulls")

    for col in rules.get("unique", []):
        if col not in df.columns:
            issues.append(f"Column missing for unique: {col}")
        else:
            dup = int(df.duplicated(subset=[col]).sum())
            if dup > 0:
                issues.append(f"Unique violation: {col} has {dup} duplicates")

    for col, bounds in rules.get("range", {}).items():
        if col not in df.columns:
            issues.append(f"Column missing for range: {col}")
        else:
            s = df[col]
            if "min" in bounds:
                v = s[s < bounds["min"]].shape[0]
                if v > 0:
                    issues.append(f"Range violation: {col} < {bounds['min']} count={v}")
            if "max" in bounds:
                v = s[s > bounds["max"]].shape[0]
                if v > 0:
                    issues.append(f"Range violation: {col} > {bounds['max']} count={v}")

    for col, allowed in rules.get("allowed_values", {}).items():
        if col not in df.columns:
            issues.append(f"Column missing for allowed_values: {col}")
        else:
            bad = df[~df[col].isin(allowed)][col]
            if bad.shape[0] > 0:
                issues.append(f"Allowed-values violation: {col} has {bad.shape[0]} out-of-domain values")

    ok = len(issues) == 0
    return ok, issues

def transform(
    df: pd.DataFrame,
    recipe: Dict[str, Any],
    aux_dfs: Optional[Dict[str, pd.DataFrame]] = None
) -> pd.DataFrame:
    """Recipe example:
    {
      "select": ["order_id","date","region","revenue","product_id"],
      "filter": "revenue >= 0 and region in ['APAC','EMEA','AMER']",
      "derive": [{"name":"date_day", "expr":"pd.to_datetime(df['date']).dt.date.astype(str)"}],
      "join": {"right_df": "regions", "on": ["region"], "how": "left"},
      "groupby": {"by": ["date_day","region"], "agg": {"revenue":"sum"}}
    }
    """
    out = df.copy()

    if "select" in recipe:
        out = out[recipe["select"]]

    if "filter" in recipe and recipe["filter"]:
        # Note: filter still uses pandas .query() over current columns
        out = out.query(recipe["filter"], engine="python")

    if "derive" in recipe:
        # Option B: Explicit df-referencing in expressions
        safe_globals = {"__builtins__": {}}
        safe_locals_base = {
            "pd": pd,
            "df": out,
            "str": str,
            "int": int,
            "float": float,
            "abs": abs,
            "round": round
        }
        for d in recipe["derive"]:
            value = eval(d["expr"], safe_globals, safe_locals_base)
            out[d["name"]] = value

    if "join" in recipe:
        j = recipe["join"]
        right_name = j["right_df"]
        if aux_dfs is None or right_name not in aux_dfs:
            raise ValueError(f"Aux DF '{right_name}' not provided for join.")
        out = out.merge(aux_dfs[right_name], on=j["on"], how=j.get("how", "left"))

    if "groupby" in recipe:
        g = recipe["groupby"]
        out = out.groupby(g["by"], dropna=False).agg(g["agg"]).reset_index()

    return out

def write_report(title: str, sections: List[Tuple[str, str]], out_dir: Optional[str] = None) -> str:
    rpt_dir = out_dir or MEM["preferences"]["report_dir"]
    rpt_dir = _safe_path(rpt_dir)
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

# ---------- Quickstart / Demo ----------
if __name__ == "__main__":
    # Create demo data if not present
    base = _safe_path(MEM["preferences"]["base_dir"])
    ensure_dir(base)
    sales_fp = os.path.join(base, "sales.csv")
    regions_fp = os.path.join(base, "regions.csv")

    if not os.path.exists(sales_fp):
        pd.DataFrame({
            "order_id": [1,2,3,4,5],
            "date": ["2025-01-01","2025-01-01","2025-01-02","2025-01-02","2025-01-02"],
            "region": ["APAC","EMEA","APAC","AMER","APAC"],
            "revenue": [1000, 800, 1200, 700, 900],
            "product_id": ["P1","P2","P1","P3","P2"]
        }).to_csv(sales_fp, index=False)

    if not os.path.exists(regions_fp):
        pd.DataFrame({
            "region": ["APAC","EMEA","AMER"],
            "region_name": ["Asia Pacific","Europe, Middle East & Africa","Americas"]
        }).to_csv(regions_fp, index=False)

    # ---- Option B: df-referencing expression ----
    recipe = {
        "select": ["order_id","date","region","revenue","product_id"],
        "derive": [
            {"name":"date_day", "expr":"pd.to_datetime(df['date']).dt.date.astype(str)"},
            {"name":"rev_in_k", "expr":"df['revenue'] / 1000"}
        ],
        "join": {"right_df": "regions", "on": ["region"], "how": "left"},
        "groupby": {"by": ["date_day","region","region_name"], "agg": {"revenue":"sum"}}
    }

    dq_rules = {
        "non_null": ["date_day","region","revenue"],
        "unique": ["order_id"],  # realistic; set "date_day" to force a failure
        "range": {"revenue": {"min": 0}},
        "allowed_values": {"region": ["APAC","EMEA","AMER"]}
    }

    out_path = os.path.join(MEM["preferences"]["output_dir"], "revenue_by_region.parquet")
    ensure_dir(_safe_path(MEM["preferences"]["output_dir"]))
    ensure_dir(_safe_path(MEM["preferences"]["report_dir"]))

    goal = "Create clean daily revenue by region with DQ and a report"
    result = run_agent(goal, {
        "sales_path": os.path.relpath(sales_fp, SAFE_ROOT),
        "regions_path": os.path.relpath(regions_fp, SAFE_ROOT),
        "recipe": recipe,
        "dq_rules": dq_rules,
        "out_path": os.path.relpath(out_path, SAFE_ROOT),
        "report_title": "Daily Revenue by Region - Agent Run"
    })

    print(json.dumps({
        "out_path": result.get("out_path"),
        "report_path": result.get("report_path"),
        "reflection_ok": result.get("reflection_ok"),
        "dq_ok": result.get("dq_ok"),
        "dq_issues": result.get("dq_issues", [])
    }, indent=2))
