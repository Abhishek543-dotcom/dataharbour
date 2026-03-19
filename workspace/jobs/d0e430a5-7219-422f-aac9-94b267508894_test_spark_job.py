#!/usr/bin/env python3
"""
Simple test Spark job for DataHarbour
"""
from pyspark.sql import SparkSession

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("DataHarbour-Test-Job") \
        .getOrCreate()
    
    # Create a simple DataFrame
    data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
    columns = ["Name", "Age"]
    
    df = spark.createDataFrame(data, columns)
    
    print("=" * 50)
    print("Test Job Started")
    print("=" * 50)
    df.show()
    print("=" * 50)
    print("Test Job Completed Successfully")
    print("=" * 50)
    
    spark.stop()
