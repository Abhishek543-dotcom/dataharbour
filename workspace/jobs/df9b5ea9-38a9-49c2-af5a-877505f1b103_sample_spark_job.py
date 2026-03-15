# Import necessary libraries
from pyspark.sql import SparkSession

# Create Spark session
spark = SparkSession.builder \
    .appName("DataHarbour Sample Job") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

print("Spark session created")
# Read JSON file from MinIO
# Assuming bucket 'data' exists in MinIO
json_path = "s3a://data/sample.json"

df = spark.read.json(json_path)
df.show()
# Write to Iceberg table
spark.sql("CREATE SCHEMA IF NOT EXISTS dataharbour")
table_name = "spark_catalog.dataharbour.sample_table"

df.writeTo(table_name).createOrReplace()
print("Data written to Iceberg table")
# Query the table
result = spark.table(table_name)
result.show()