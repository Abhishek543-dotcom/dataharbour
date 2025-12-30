"""
Sample ETL PySpark Job for DataHarbour
=======================================
This job demonstrates a complete ETL workflow:
1. Read CSV from MinIO (S3-compatible storage)
2. Perform data transformations
3. Write to Delta Lake on MinIO (for analytics)
4. Write to PostgreSQL (for operational queries)

Use Case: Customer Orders Analytics
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, count, avg, year, month, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType
from datetime import datetime

# Initialize Spark Session with Delta Lake and S3 support
spark = SparkSession.builder \
    .appName("DataHarbour ETL - Customer Orders") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

print("=" * 80)
print("DataHarbour ETL Job Started")
print("=" * 80)

# Step 1: Read CSV from MinIO
print("\n[STEP 1] Reading CSV from MinIO bucket 'data-lake'...")
input_path = "s3a://data-lake/raw/orders.csv"

# Define schema for better performance
schema = StructType([
    StructField("order_id", IntegerType(), False),
    StructField("customer_id", IntegerType(), False),
    StructField("product", StringType(), False),
    StructField("quantity", IntegerType(), False),
    StructField("price", DoubleType(), False),
    StructField("order_date", DateType(), False),
    StructField("region", StringType(), False)
])

try:
    # Read CSV with schema
    df_orders = spark.read \
        .format("csv") \
        .option("header", "true") \
        .schema(schema) \
        .load(input_path)

    print(f"✓ Successfully read {df_orders.count()} orders from MinIO")
    print("\nSample data:")
    df_orders.show(5, truncate=False)

except Exception as e:
    print(f"✗ Failed to read from MinIO: {e}")
    print("Creating sample data instead...")

    # Create sample data if MinIO bucket doesn't exist
    from pyspark.sql import Row
    sample_data = [
        Row(1, 101, "Laptop", 1, 1200.00, datetime(2024, 1, 15).date(), "North"),
        Row(2, 102, "Mouse", 2, 25.00, datetime(2024, 1, 16).date(), "South"),
        Row(3, 103, "Keyboard", 1, 75.00, datetime(2024, 1, 17).date(), "East"),
        Row(4, 101, "Monitor", 2, 300.00, datetime(2024, 1, 18).date(), "North"),
        Row(5, 104, "Laptop", 1, 1200.00, datetime(2024, 1, 19).date(), "West"),
        Row(6, 102, "Mouse", 3, 25.00, datetime(2024, 1, 20).date(), "South"),
        Row(7, 105, "Keyboard", 2, 75.00, datetime(2024, 1, 21).date(), "East"),
        Row(8, 103, "Monitor", 1, 300.00, datetime(2024, 1, 22).date(), "North"),
        Row(9, 104, "Laptop", 1, 1200.00, datetime(2024, 1, 23).date(), "West"),
        Row(10, 105, "Mouse", 5, 25.00, datetime(2024, 1, 24).date(), "South")
    ]
    df_orders = spark.createDataFrame(sample_data, schema)
    print(f"✓ Created sample dataset with {df_orders.count()} orders")

# Step 2: Data Transformation
print("\n[STEP 2] Performing data transformations...")

# Add calculated column: total_amount
df_orders = df_orders.withColumn("total_amount", col("quantity") * col("price"))

# Add ETL metadata
df_orders = df_orders.withColumn("etl_timestamp", current_timestamp())

# Create aggregated view: Sales by Region
df_sales_by_region = df_orders.groupBy("region").agg(
    count("order_id").alias("total_orders"),
    _sum("total_amount").alias("total_revenue"),
    avg("total_amount").alias("avg_order_value")
).orderBy(col("total_revenue").desc())

print("✓ Transformations completed")
print("\nSales by Region:")
df_sales_by_region.show(truncate=False)

# Create aggregated view: Sales by Product
df_sales_by_product = df_orders.groupBy("product").agg(
    count("order_id").alias("total_orders"),
    _sum("quantity").alias("total_quantity"),
    _sum("total_amount").alias("total_revenue")
).orderBy(col("total_revenue").desc())

print("\nSales by Product:")
df_sales_by_product.show(truncate=False)

# Step 3: Write to Delta Lake on MinIO
print("\n[STEP 3] Writing to Delta Lake on MinIO...")
delta_path = "s3a://data-lake/delta/orders"

try:
    # Write as Delta table (supports ACID transactions, time travel, schema evolution)
    df_orders.write \
        .format("delta") \
        .mode("overwrite") \
        .save(delta_path)

    print(f"✓ Successfully wrote Delta table to: {delta_path}")

    # Write aggregated tables
    df_sales_by_region.write \
        .format("delta") \
        .mode("overwrite") \
        .save("s3a://data-lake/delta/sales_by_region")

    df_sales_by_product.write \
        .format("delta") \
        .mode("overwrite") \
        .save("s3a://data-lake/delta/sales_by_product")

    print("✓ Successfully wrote aggregated Delta tables")

except Exception as e:
    print(f"⚠ Delta write failed (bucket may not exist): {e}")
    print("  To fix: Create 'data-lake' bucket in MinIO via Storage page")

# Step 4: Write to PostgreSQL
print("\n[STEP 4] Writing to PostgreSQL...")

# PostgreSQL connection properties
postgres_url = "jdbc:postgresql://postgres:5432/dataharbour"
postgres_properties = {
    "user": "admin",
    "password": "admin",
    "driver": "org.postgresql.Driver"
}

try:
    # Write orders table
    df_orders.write \
        .jdbc(url=postgres_url, table="etl_orders", mode="overwrite", properties=postgres_properties)

    print("✓ Successfully wrote 'etl_orders' table to PostgreSQL")

    # Write aggregated tables
    df_sales_by_region.write \
        .jdbc(url=postgres_url, table="etl_sales_by_region", mode="overwrite", properties=postgres_properties)

    df_sales_by_product.write \
        .jdbc(url=postgres_url, table="etl_sales_by_product", mode="overwrite", properties=postgres_properties)

    print("✓ Successfully wrote aggregated tables to PostgreSQL")
    print("\n  You can now query these tables in the Database page:")
    print("  - etl_orders")
    print("  - etl_sales_by_region")
    print("  - etl_sales_by_product")

except Exception as e:
    print(f"✗ PostgreSQL write failed: {e}")
    print("  This might be due to missing PostgreSQL JDBC driver")

# Step 5: Summary
print("\n" + "=" * 80)
print("ETL Job Summary")
print("=" * 80)
print(f"Total Records Processed: {df_orders.count()}")
print(f"Total Revenue: ${df_sales_by_region.agg(_sum('total_revenue')).collect()[0][0]:,.2f}")
print(f"Regions Analyzed: {df_sales_by_region.count()}")
print(f"Products Analyzed: {df_sales_by_product.count()}")
print("\nData Outputs:")
print(f"  1. Delta Lake (MinIO): {delta_path}")
print(f"  2. PostgreSQL Tables: etl_orders, etl_sales_by_region, etl_sales_by_product")
print("\nETL Job Completed Successfully! ✓")
print("=" * 80)

# Stop Spark session
spark.stop()
