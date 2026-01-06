from typing import Any, Dict
import os
import json
import pandas as pd
from mcp.server.fastmcp import FastMCP, Context

from agent.agent_recipe_generator import generate_recipe_from_prompt
from agent.llm_client import LLMClient
from agent import orchestrator
import datetime

def register_tools(mcp: FastMCP):
    @mcp.tool()
    def get_system_time() -> str:
        """Returns the current system time"""
        return datetime.datetime.now().isoformat()

    @mcp.tool()
    def generate_data_recipe(prompt: str, sales_path: str, regions_path: str = None, out_path: str = "output.csv") -> str:
        """
        Generates and runs a data transformation recipe based on a natural language prompt.
        
        Args:
            prompt: The user's request (e.g., "Calculate monthly revenue by region")
            sales_path: Path to the sales CSV file
            regions_path: Path to the regions CSV file (optional)
            out_path: Path to save the result CSV
        """
        # Build context from files
        context_lines = []
        try:
            cols = pd.read_csv(sales_path, nrows=0).columns.tolist()
            context_lines.append(f"- sales: {cols}")
        except Exception:
            pass
            
        if regions_path:
            try:
                cols = pd.read_csv(regions_path, nrows=0).columns.tolist()
                context_lines.append(f"- regions: {cols}")
            except Exception:
                pass
        
        dataset_context = "\n".join(context_lines) if context_lines else ""
        
        # Generator
        llm = LLMClient() # Uses env vars
        recipe = generate_recipe_from_prompt(prompt, llm, dataset_context=dataset_context)
        
        # Execution
        inputs = {
            "sales_path": sales_path,
            "regions_path": regions_path,
            "recipe": recipe,
            "out_path": out_path,
            "dq_rules": {},
            "report_title": f"MCP Request: {prompt}"
        }
        
        result = orchestrator.run_agent(inputs["report_title"], inputs)
        
        # Helper to prettify paths for the LLM
        def to_rel(p):
            try:
                return os.path.relpath(p) if p else "None"
            except:
                return str(p)

        return f"Recipe executed. Report: {to_rel(result.get('report_path'))}. Output saved to: {to_rel(result.get('out_path'))}"
