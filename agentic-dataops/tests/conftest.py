
import os
import sys

import pytest

# Ensure src/ is on import path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import agent.memory as mem


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """Isolated SAFE_ROOT sandbox under tmp_path.
    Also redirects memory file under tmp_path.
    """
    monkeypatch.setattr(mem, 'SAFE_ROOT', str(tmp_path))
    monkeypatch.setattr(mem, 'MEMORY_FILE', os.path.join(str(tmp_path), 'agent_memory.json'))
    # Ensure prefs dirs exist within sandbox
    for d in [mem.MEM['preferences']['base_dir'], mem.MEM['preferences']['output_dir'], mem.MEM['preferences']['report_dir']]:
        p = os.path.join(str(tmp_path), d)
        os.makedirs(p, exist_ok=True)
    return tmp_path
