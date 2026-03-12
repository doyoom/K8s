"""
NOTE:
이 파일은 `K8s/spark-code-configmap.yaml`에 포함되던 Spark Streaming 코드를
컨테이너 이미지에 직접 포함시키기 위해 분리한 버전입니다.
"""

from __future__ import annotations

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    dayofmonth,
    hour,
    lit,
    month,
    regexp_extract,
    substring,
    to_timestamp,
    udf,
    when,
    year,
)
from pyspark.sql.types import StringType

from spark_app.parsing import extract_action_type, extract_endpoint


def main() -> None:
    kafka_bootstrap = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "streaming-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092",
    )
    topic = os.getenv("KAFKA_TOPIC", "user-activity-logs")
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio.storage.svc.cluster.local:9000")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY", "admin")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY", "password1234")
    silver_path = os.getenv("SILVER_PATH", "s3a://mybucket/silver/user-activity-v2")
    checkpoint_path = os.getenv("CHECKPOINT_PATH", "/tmp/checkpoints/user-activity")

    spark = SparkSession.builder.appName("KafkaToMinIO_Silver").getOrCreate()

    hadoop_conf = spark._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.endpoint", minio_endpoint)
    hadoop_conf.set("fs.s3a.access.key", minio_access_key)
    hadoop_conf.set("fs.s3a.secret.key", minio_secret_key)
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hadoop_conf.set("fs.s3a.path.style.access", "true")

    hadoop_conf.setInt("fs.s3a.connection.timeout", 60000)
    hadoop_conf.setInt("fs.s3a.connection.establish.timeout", 60000)
    hadoop_conf.setInt("fs.s3a.attempts.maximum", 10)

    spark.sparkContext.setLogLevel("WARN")

    extract_action_type_udf = udf(extract_action_type, StringType())
    extract_endpoint_udf = udf(extract_endpoint, StringType())

    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    bronze_df = df.selectExpr(
        "CAST(value AS STRING) AS raw_json",
        "topic",
        "partition",
        "offset",
        "CAST(timestamp AS STRING) AS kafka_timestamp",
    )

    cleaned_df = bronze_df.withColumn(
        "raw_json_clean",
        regexp_extract(col("raw_json"), r"^.*?(\[[A-Z_]+.*)", 1),
    )

    parsed_df = (
        cleaned_df.withColumn("event_type", regexp_extract(col("raw_json_clean"), r"\[([A-Z_]+)\]", 1))
        .withColumn("event_timestamp_str", regexp_extract(col("raw_json_clean"), r"\] ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:.]+)", 1))
        .withColumn("event_timestamp", to_timestamp(col("event_timestamp_str"), "yyyy-MM-dd HH:mm:ss.SSS"))
        .withColumn("action_type", extract_action_type_udf(col("raw_json_clean")))
        .withColumn("endpoint", extract_endpoint_udf(col("raw_json_clean")))
        .withColumn("user_id", regexp_extract(col("raw_json_clean"), r"userId=([0-9]+)", 1).cast("long"))
        .withColumn("message", substring(col("raw_json_clean"), 1, 1000))
        .withColumn("year", year(col("event_timestamp")))
        .withColumn("month", month(col("event_timestamp")))
        .withColumn("day", dayofmonth(col("event_timestamp")))
        .withColumn("hour", hour(col("event_timestamp")))
    )

    # Basic data quality flags (lightweight, safe)
    enriched_df = (
        parsed_df.withColumn("is_valid_timestamp", col("event_timestamp").isNotNull())
        .withColumn("is_valid_user", when(col("user_id").isNull(), lit(False)).otherwise(lit(True)))
        .withColumn("is_valid_endpoint", when(col("endpoint").isNull(), lit(False)).otherwise(lit(True)))
    )

    (
        enriched_df.writeStream.format("parquet")
        .option("path", silver_path)
        .option("checkpointLocation", checkpoint_path)
        .outputMode("append")
        .start()
        .awaitTermination()
    )


if __name__ == "__main__":
    main()

