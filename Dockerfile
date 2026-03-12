FROM apache/spark:3.5.1

# Portfolio-friendly image:
# - ships the Spark job code as a real image artifact
# - supports running on Kubernetes without ConfigMap-mounted code

USER root
WORKDIR /opt/spark/code

COPY spark_app/user_activity_streaming.py /opt/spark/code/user_activity_streaming.py

USER 185

# Default command is intentionally minimal; k8s manifests define spark-submit args.
CMD ["/opt/spark/bin/spark-submit", "--version"]
