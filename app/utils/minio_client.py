from minio import Minio

client = Minio(
    endpoint="localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

bucket_name = "files"
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name=bucket_name)
