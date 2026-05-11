FROM apache/spark:3.5.1

USER root
WORKDIR /opt/spark/code

COPY spark_app/user_activity_streaming.py /opt/spark/code/user_activity_streaming.py

USER 185

CMD ["/opt/spark/bin/spark-submit", "--version"]
