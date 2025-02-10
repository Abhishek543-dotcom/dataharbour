# Use a base image with Java 11
FROM openjdk:11

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3 python3-pip wget postgresql-client

# Set environment variables for Spark and Hadoop
ENV SPARK_VERSION=3.3.0
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark
ENV PATH="$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH"

# Download and extract Spark
RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
    && tar xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -C /opt \
    && mv /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} $SPARK_HOME \
    && rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz

# Install Python libraries
RUN pip3 install pyspark==${SPARK_VERSION} jupyter delta-spark minio psycopg2-binary apache-airflow

# Create data directories for Hive metastore and warehouse
RUN mkdir -p /data

# Configure Hive
COPY hive-site.xml $SPARK_HOME/conf/hive-site.xml

# Add Delta Lake JARs to Spark
RUN wget -q https://repo1.maven.org/maven2/io/delta/delta-core_2.12/2.4.0/delta-core_2.12-2.4.0.jar -P $SPARK_HOME/jars/

# Configure Spark for Delta Lake
COPY spark-defaults.conf $SPARK_HOME/conf/spark-defaults.conf

# Entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Jupyter Notebook and Airflow ports
EXPOSE 8888 8080

# Start the container
ENTRYPOINT ["/entrypoint.sh"]