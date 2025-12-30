import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DATA_DIR = Path("data").resolve()

def register_resources(mcp: FastMCP):
    @mcp.resource("file://data/{filename}")
    def get_data_file(filename: str) -> str:
        """Read a CSV file from the data directory"""
        file_path = DATA_DIR / filename
        
        # Security check: ensure we don't escape data dir
        if not str(file_path.resolve()).startswith(str(DATA_DIR)):
             raise ValueError("Access denied")
             
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found")
            
        return file_path.read_text(encoding="utf-8")
