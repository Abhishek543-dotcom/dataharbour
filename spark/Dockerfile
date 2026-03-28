FROM apache/spark:3.5.0

LABEL maintainer="DataHarbour Team"
LABEL description="Spark with Iceberg, Hadoop-AWS, and PostgreSQL JDBC"

USER root

# Download required JARs for:
# 1. Apache Iceberg — open table format (ACID, schema evolution, time travel)
# 2. Hadoop AWS — S3A filesystem for MinIO access
# 3. AWS SDK — underlying SDK for S3 operations
# 4. PostgreSQL JDBC — connect Spark to PostgreSQL
RUN wget -q -P /opt/spark/jars/ \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.4.3/iceberg-spark-runtime-3.5_2.12-1.4.3.jar && \
    wget -q -P /opt/spark/jars/ \
    https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    wget -q -P /opt/spark/jars/ \
    https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.540/aws-java-sdk-bundle-1.12.540.jar && \
    wget -q -P /opt/spark/jars/ \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar

# Create workspace directories
RUN mkdir -p /workspace/jobs /workspace/logs /workspace/notebooks /workspace/data /workspace/iceberg

USER spark
