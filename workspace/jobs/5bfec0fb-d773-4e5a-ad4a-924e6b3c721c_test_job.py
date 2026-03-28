from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('test').getOrCreate()
print('DataHarbour test job executed successfully')
spark.stop()
