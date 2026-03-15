# Logic to submit jobs to Spark Master
from pyspark.sql import SparkSession

def submit_job(job_path):
    spark = SparkSession.builder.appName("DataHarbour").getOrCreate()
    # Submit job logic here
    pass