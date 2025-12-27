# add/ensure these
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

MEMORY_FILE = "agent_memory.json"

__all__ = ["MEM", "SAFE_ROOT", "safe_path", "ensure_dir", "load_memory", "save_memory"]

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

def safe_path(*parts: str) -> str:
    """Resolve paths inside SAFE_ROOT; allow absolute paths only if under SAFE_ROOT."""
    joined = os.path.join(*parts)
    root = os.path.normcase(os.path.realpath(SAFE_ROOT))

    # If relative -> anchor to SAFE_ROOT; if absolute -> keep as is
    candidate = (
        os.path.normcase(os.path.realpath(os.path.join(SAFE_ROOT, joined)))
        if not os.path.isabs(joined) else
        os.path.normcase(os.path.realpath(joined))
    )

    # Allow SAFE_ROOT or any subpath
    if not (candidate == root or candidate.startswith(root + os.sep)):
        raise ValueError("Access outside working directory is not allowed.")
    return candidate
