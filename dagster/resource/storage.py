import os

RAW_PREFIX = "s3://lake/raw/"
CURATED_PREFIX = "s3://lake/curated/"
MINIO_ENDPOINT = os.getenv("AWS_S3_ENDPOINT", "http://minio:9000")
