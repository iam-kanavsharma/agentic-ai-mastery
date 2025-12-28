# add/ensure these
from __future__ import annotations

import ast
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from agent.memory import MEM, SAFE_ROOT, safe_path


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

# ---------- Tools ----------
def list_datasets(base_dir: Optional[str] = None) -> List[str]:
    base = base_dir or MEM["preferences"]["base_dir"]
    base = safe_path(base)
    ensure_dir(base)
    items = []
    for root, _, files in os.walk(base):
        for fn in files:
            if fn.lower().endswith((".csv", ".parquet")):
                items.append(os.path.relpath(os.path.join(root, fn), SAFE_ROOT))
    return sorted(items)

def load_df(path: str) -> pd.DataFrame:
    full = safe_path(path)
    if path.lower().endswith(".csv"):
        return pd.read_csv(full)
    if path.lower().endswith(".parquet"):
        return pd.read_parquet(full)
    raise ValueError("Unsupported file type. Use .csv or .parquet")

def save_df(df: pd.DataFrame, out_path: str):
    full = safe_path(out_path)
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
        
        # force out to be an independent object before writing
        out = out.copy(deep=True)

        # Use a safe AST-validated evaluator instead of raw eval
        def _get_root_name(node: ast.AST) -> Optional[str]:
            if isinstance(node, ast.Name):
                return node.id
            if isinstance(node, ast.Attribute):
                return _get_root_name(node.value)
            if isinstance(node, ast.Subscript):
                return _get_root_name(node.value)
            if isinstance(node, ast.Call):
                # For chained calls like pd.to_datetime(...).dt.date.astype(...)
                return _get_root_name(node.func)
            return None

        class _SafeVisitor(ast.NodeVisitor):
            def __init__(self, allowed_names: set, allowed_roots: set):
                self.allowed_names = allowed_names
                self.allowed_roots = allowed_roots

            def visit_Name(self, node: ast.Name) -> None:
                if node.id not in self.allowed_names:
                    raise ValueError(f"Use of name '{node.id}' is not allowed in derived expressions")

            def visit_Call(self, node: ast.Call) -> None:
                root = _get_root_name(node.func)
                if root is None or root not in self.allowed_roots:
                    raise ValueError(f"Function calls to '{root}' are not allowed in derived expressions")
                self.generic_visit(node)

            def visit_Attribute(self, node: ast.Attribute) -> None:
                if node.attr.startswith("__"):
                    raise ValueError("Access to dunder attributes is not allowed")
                self.generic_visit(node)

            def visit_Lambda(self, node: ast.Lambda) -> None:
                raise ValueError("Lambdas are not allowed in derived expressions")

            def visit_ListComp(self, node: ast.ListComp) -> None:
                raise ValueError("Comprehensions are not allowed in derived expressions")

            def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
                raise ValueError("Comprehensions are not allowed in derived expressions")

            def visit_Import(self, node: ast.Import) -> None:
                raise ValueError("Import statements are not allowed in derived expressions")

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                raise ValueError("Import statements are not allowed in derived expressions")

        def safe_eval(expr: str, safe_locals: Dict[str, Any]) -> Any:
            try:
                node = ast.parse(expr, mode="eval")
            except SyntaxError as e:
                raise ValueError("Invalid expression syntax") from e

            allowed_names = set(safe_locals.keys())
            allowed_roots = allowed_names
            visitor = _SafeVisitor(allowed_names, allowed_roots)
            visitor.visit(node)

            return eval(compile(node, "<safe_eval>", "eval"), {"__builtins__": {}}, safe_locals)

        safe_locals_base = {
            "pd": pd,
            "df": out,   # explicit reference
            "str": str,
            "int": int,
            "float": float,
            "abs": abs,
            "round": round
        }

        # Build all derived columns first, then assign once (avoids intermediate warns)
        new_cols = {}
        for d in recipe["derive"]:
            name = d["name"]
            val = safe_eval(d["expr"], safe_locals_base)
            new_cols[name] = val

        out = out.assign(**new_cols)

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

