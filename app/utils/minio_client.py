from minio import Minio

client = Minio(
    endpoint="localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

RESOURCE_BUCKET_NAME = "files"
NOTE_BUCKET_NAME = "notes"
if not client.bucket_exists(RESOURCE_BUCKET_NAME):
    client.make_bucket(bucket_name=RESOURCE_BUCKET_NAME)

if not client.bucket_exists(NOTE_BUCKET_NAME):
    client.make_bucket(bucket_name=NOTE_BUCKET_NAME)
