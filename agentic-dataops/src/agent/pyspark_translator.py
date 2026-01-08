from typing import Dict, Any

def translate_recipe_to_pyspark(recipe: Dict[str, Any], sales_path: str, regions_path: str, out_path: str) -> str:
    """
    Converts a JSON data recipe into a standalone PySpark script.
    """
    script = [
        "from pyspark.sql import SparkSession",
        "from pyspark.sql.functions import *",
        "",
        "spark = SparkSession.builder.appName('AgenticDataOps').getOrCreate()",
        "",
        "# 1. Load Data",
        f"# Assuming paths are accessible to the cluster (e.g. DBFS/S3)",
        f"# For demo purposes, using input paths strictly.",
        f"df_sales = spark.read.csv('{sales_path}', header=True, inferSchema=True)",
    ]
    
    if "join" in recipe and regions_path:
        script.append(f"df_regions = spark.read.csv('{regions_path}', header=True, inferSchema=True)")

    script.append("")
    script.append("# 2. Transformations")
    script.append("df = df_sales")
    
    # Filter
    if "filter" in recipe:
        # Note: We trust the LLM generated valid SparkSQL expression or simple filter
        script.append(f"df = df.filter(\"{recipe['filter']}\")")
        
    # Join
    if "join" in recipe:
        j = recipe["join"]
        # j: {right_df, on, how}
        # In Spark: df.join(other, on, how)
        right_name = "df_" + j["right_df"]
        on_cols = j["on"]
        how = j.get("how", "inner")
        script.append(f"df = df.join({right_name}, on={on_cols}, how='{how}')")

    # Derive
    if "derive" in recipe:
        for d in recipe["derive"]:
            # d: {name, expr}
            # Spark: df.withColumn(name, expr)
            # The expr usually needs to be a Column object, so we rely on the LLM generating "col('x') + 1"
            # Since we did "from pyspark.sql.functions import *", strings like "col('date')" work if eval'd, 
            # but usually selectExpr is safer for string expressions?
            # Actually, let's use selectExpr if it's a pure SQL string?
            # Or assume the LLM provided valid Python code string for the expr.
            # Example: "year(col('date'))" -> Valid if inserted as argument.
            script.append(f"df = df.withColumn('{d['name']}', {d['expr']})")

    # GroupBy
    if "groupby" in recipe:
        g = recipe["groupby"]
        # g: {by: [], agg: {col: func}}
        by_cols = g["by"]
        aggs = []
        for col, func in g["agg"].items():
            # Spark: sum(col)
            aggs.append(f"{func}('{col}').alias('{col}')")
        
        agg_str = ", ".join(aggs)
        script.append(f"df = df.groupby({by_cols}).agg({agg_str})")

    # Select
    if "select" in recipe:
        cols = recipe["select"]
        # If groupby happened, cols must match aggregated cols.
        # Spark naturally handles this if we just select what exists.
        script.append(f"df = df.select({cols})")

    script.append("")
    script.append("# 3. Output")
    script.append(f"# Writing to single CSV for simple retrieval")
    script.append(f"df.coalesce(1).write.mode('overwrite').csv('{out_path}', header=True)")
    script.append("print('PySpark Job Completed Successfully')")
    
    return "\n".join(script)
