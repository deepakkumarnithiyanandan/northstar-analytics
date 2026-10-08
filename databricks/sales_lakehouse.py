# Databricks notebook source
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType


dbutils.widgets.text("source_path", "/Volumes/workspace/northstar_sales/sales/sample_sales.csv")
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "northstar_sales")

# COMMAND ----------

source_path = dbutils.widgets.get("source_path")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
namespace = f"{catalog}.{schema}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {namespace}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {namespace}.sales")

raw = (
    spark.read.option("header", True)
    .option("mode", "FAILFAST")
    .csv(source_path)
)
raw.write.format("delta").mode("overwrite").saveAsTable(f"{namespace}.bronze_sales")

columns = {name.lower(): name for name in raw.columns}
required = {
    "order_id", "order_date", "customer_id", "product", "category",
    "region", "quantity", "unit_price",
}
missing = sorted(required - set(columns))
if missing:
    raise ValueError(f"Sales source is missing required columns: {', '.join(missing)}")

def source_column(name):
    return F.col(f"`{columns[name]}`")


revenue = (
    source_column("revenue").cast(DecimalType(18, 2))
    if "revenue" in columns
    else F.lit(None).cast(DecimalType(18, 2))
)

silver = raw.select(
    F.trim(source_column("order_id")).alias("order_id"),
    F.to_date(source_column("order_date")).alias("order_date"),
    F.trim(source_column("customer_id")).alias("customer_id"),
    F.trim(source_column("product")).alias("product_name"),
    F.trim(source_column("category")).alias("category"),
    F.trim(source_column("region")).alias("region"),
    source_column("quantity").cast("int").alias("quantity"),
    source_column("unit_price").cast(DecimalType(18, 2)).alias("unit_price"),
    revenue.alias("source_revenue"),
)
silver = silver.withColumn(
    "revenue",
    F.coalesce(F.col("source_revenue"), (F.col("quantity") * F.col("unit_price")).cast(DecimalType(18, 2))),
).drop("source_revenue")

invalid = silver.filter(
    F.col("order_id").isNull() | (F.col("order_id") == "")
    | F.col("order_date").isNull()
    | F.col("customer_id").isNull() | (F.col("customer_id") == "")
    | F.col("product_name").isNull() | (F.col("product_name") == "")
    | F.col("category").isNull() | (F.col("category") == "")
    | F.col("region").isNull() | (F.col("region") == "")
    | F.col("quantity").isNull() | (F.col("quantity") <= 0)
    | F.col("unit_price").isNull() | (F.col("unit_price") < 0)
    | F.col("revenue").isNull() | (F.col("revenue") < 0)
)
invalid_count = invalid.count()
if invalid_count:
    raise ValueError(f"Sales source contains {invalid_count} invalid row(s); inspect bronze_sales.")

duplicate_count = (
    silver.groupBy("order_id").count().filter(F.col("count") > 1).count()
)
if duplicate_count:
    raise ValueError(f"Expected one row per order_id; found {duplicate_count} duplicate order(s).")

silver.write.format("delta").mode("overwrite").saveAsTable(f"{namespace}.silver_sales")

gold = (
    silver.withColumn("date_id", F.date_format("order_date", "yyyyMMdd").cast("int"))
    .withColumn("order_year", F.year("order_date"))
    .withColumn("order_quarter", F.quarter("order_date"))
    .withColumn("order_month", F.month("order_date"))
    .withColumn("product_id", F.sha2(F.concat_ws("||", "product_name", "category"), 256))
    .select(
        "order_id", "order_date", "date_id", "order_year", "order_quarter",
        "order_month", "customer_id", "product_id", "product_name", "category", "region",
        "quantity", "unit_price", "revenue",
    )
)
gold.write.format("delta").mode("overwrite").saveAsTable(f"{namespace}.sales_gold")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.dim_date AS
SELECT DISTINCT
    date_id,
    order_date,
    order_year,
    order_quarter,
    order_month,
    date_format(order_date, 'MMM') AS month_name
FROM {namespace}.sales_gold
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.dim_product AS
SELECT DISTINCT product_id, product_name, category
FROM {namespace}.sales_gold
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.dim_customer AS
SELECT DISTINCT customer_id
FROM {namespace}.sales_gold
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.dim_region AS
SELECT DISTINCT region
FROM {namespace}.sales_gold
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.fact_sales AS
SELECT order_id, date_id, customer_id, product_id, region, quantity, unit_price, revenue
FROM {namespace}.sales_gold
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.monthly_sales AS
SELECT
    date_trunc('MONTH', order_date) AS sales_month,
    order_year,
    order_quarter,
    order_month,
    region,
    category,
    SUM(revenue) AS revenue,
    SUM(quantity) AS units_sold,
    COUNT(*) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count,
    CASE WHEN COUNT(*) > 0 THEN SUM(revenue) / COUNT(*) ELSE 0 END AS average_order_value
FROM {namespace}.sales_gold
GROUP BY 1, 2, 3, 4, 5, 6
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.product_performance AS
SELECT
    product_id,
    product_name,
    category,
    SUM(revenue) AS revenue,
    SUM(quantity) AS units_sold,
    COUNT(*) AS order_count,
    CASE WHEN COUNT(*) > 0 THEN SUM(revenue) / COUNT(*) ELSE 0 END AS average_order_value
FROM {namespace}.sales_gold
GROUP BY product_id, product_name, category
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {namespace}.regional_performance AS
SELECT
    region,
    category,
    SUM(revenue) AS revenue,
    SUM(quantity) AS units_sold,
    COUNT(*) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count
FROM {namespace}.sales_gold
GROUP BY region, category
""")

print(f"Published {gold.count()} order rows from {source_path} to {namespace}.sales_gold and created BI views.")