import os
import time
import base64
from mcp.server.fastmcp import FastMCP
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs, compute

from agent.agent_recipe_generator import generate_recipe_from_prompt
from agent.llm_client import LLMClient
from agent.reviewer_agent import ReviewerAgent
from agent.pyspark_translator import translate_recipe_to_pyspark

def register_databricks_tools(mcp: FastMCP):
    @mcp.tool()
    def generate_databricks_job(prompt: str, sales_path: str = "dbfs:/FileStore/sales.csv", regions_path: str = "dbfs:/FileStore/regions.csv", out_path: str = "dbfs:/FileStore/output.csv") -> str:
        """
        Orchestrates a Databricks Job: Prompt -> Recipe (PySpark) -> Review -> PySpark Code -> Submit.
        """
        llm = LLMClient()
        
        # 1. Generate Recipe (PySpark Dialect)
        recipe = generate_recipe_from_prompt(prompt, llm, dialect="pyspark")
        if "clarification" in recipe:
            return f"CLARIFICATION NEEDED: {recipe['clarification']}"

        # 2. Reviewer Gate
        reviewer = ReviewerAgent(llm=llm)
        review = reviewer.review_recipe(prompt, recipe, context="Dialect: PySpark")
        if not review.approved:
            return f"JOB REJECTED by Reviewer: {review.feedback}"

        # 3. Translate to Code
        pyspark_code = translate_recipe_to_pyspark(recipe, sales_path, regions_path, out_path)
        
        # 4. Submit Job (Reusing the logic from submit_databricks_job, or calling it if we exposed it as a helper)
        # Since submit_databricks_job is inside the closure, we can't call it easily unless we refactor.
        # Let's call the inner logic helpers or just recurse via tool invocation? 
        # Better: Refactor submit logic to a helper function. For now, inline it or call the specific logic.
        
        # Let's just call the helper function `submit_job_logic` (we need to define it).
        # Or simpler: Just call the submit_databricks_job tool function directly if we assign it to a var?
        # FastMCP tools are wrapped.
        
        # Let's execute the submit logic directly here for simplicity or duplicate it slightly. 
        # actually, I'll allow submit_databricks_job to be called by the user manually, 
        # but here I will just do the submission.
        
        return _submit_to_databricks(pyspark_code, job_name=f"MCP_{int(time.time())}")

    @mcp.tool()
    def submit_databricks_job(script_content: str, job_name: str, cluster_id: str = None) -> str:
        """
        Submits a PySpark script to run on Databricks.
        
        Args:
            script_content: The actual PySpark code to run.
            job_name: Name for the job (used for file naming too).
            cluster_id: Optional ID of an existing cluster. If None, tries to find one or fails.
        """
        host = os.environ.get("DATABRICKS_HOST")
        token = os.environ.get("DATABRICKS_TOKEN")
        
        if not host or not token:
            return "ERROR: Missing DATABRICKS_HOST or DATABRICKS_TOKEN environment variables."

        w = WorkspaceClient(host=host, token=token)
        
        # 1. Upload Script to Workspace
        # We'll use a standard path
        file_path = f"/Shared/Agent_Jobs/{job_name}_{int(time.time())}.py"
        encoded_content = base64.b64encode(script_content.encode("utf-8")).decode("utf-8")
        
        try:
            # Check if directory exists, if not create logic (omitted for brevity, assuming /Shared exists)
            w.workspace.import_(
                path=file_path,
                format="SOURCE",
                language="PYTHON",
                content=encoded_content,
                overwrite=True
            )
        except Exception as e:
            return f"ERROR: Failed to upload script to {file_path}. Details: {str(e)}"

        # 2. Resolve Cluster
        if not cluster_id:
            # Try to pick the first running cluster
            clusters = w.clusters.list()
            running = [c for c in clusters if c.state == compute.State.RUNNING]
            if running:
                cluster_id = running[0].cluster_id
            else:
                return "ERROR: No ClusterID provided and no running clusters found."

        # 3. Create & Run Job
        try:
            run = w.jobs.submit(
                run_name=f"MCP_Run_{job_name}",
                tasks=[
                    jobs.RunTask(
                        task_key="pyspark_task",
                        existing_cluster_id=cluster_id,
                        spark_python_task=jobs.SparkPythonTask(
                            python_file=file_path
                        )
                    )
                ]
            ).result() # Wait for completion (blocking)
        except Exception as e:
             return f"ERROR: Job failed to start or crash. Details: {str(e)}"
             
        # 4. Get Output
        # output = w.jobs.get_run_output(run.run_id) 
        # Note: getting stdout logs can be tricky via SDK without external logging setup,
        # but the run_page_url is the best artifact.
        
        return f"Job Completed. Status: {run.state.life_cycle_state}. View Run: {run.run_page_url}"

def _submit_to_databricks(script_content: str, job_name: str, cluster_id: str = None) -> str:
    """Helper to submit jobs without tool overhead."""
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
        
    if not host or not token:
        return f"MOCK MODE (No Env Vars): Would submit PySpark job '{job_name}' to Databricks.\nCode Preview:\n{script_content[:200]}..."

    w = WorkspaceClient(host=host, token=token)
    
    # Upload
    file_path = f"/Shared/Agent_Jobs/{job_name}.py"
    encoded_content = base64.b64encode(script_content.encode("utf-8")).decode("utf-8")
    try:
        w.workspace.import_(path=file_path, format="SOURCE", language="PYTHON", content=encoded_content, overwrite=True)
    except Exception as e:
        return f"ERROR: Failed to upload script to {file_path}. Details: {str(e)}"

    # Cluster
    if not cluster_id:
        clusters = w.clusters.list()
        running = [c for c in clusters if c.state == compute.State.RUNNING]
        if running:
            cluster_id = running[0].cluster_id
        else:
            return "ERROR: No ClusterID provided and no running clusters found."

    # Run
    try:
        run = w.jobs.submit(
            run_name=f"MCP_Run_{job_name}",
            tasks=[jobs.RunTask(task_key="pyspark_task", existing_cluster_id=cluster_id, spark_python_task=jobs.SparkPythonTask(python_file=file_path))]
        ).result()
    except Exception as e:
            return f"ERROR: Job failed to start. Details: {str(e)}"
            
    return f"Job Completed. Status: {run.state.life_cycle_state}. View Run: {run.run_page_url}"
