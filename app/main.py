from fastapi import FastAPI, UploadFile
from minio import Minio

app = FastAPI()

client = Minio(
    endpoint="localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

@app.get("/")
def read_root():
    return {"message": "Welcome to LarngearLM-Backend API"}

@app.post("/upload-file/")
async def upload_file(uploaded_file: UploadFile):
    client.put_object(
        bucket_name="pdfs",
        object_name=uploaded_file.filename,
        data=uploaded_file.file,
        length=uploaded_file.size,
        content_type=uploaded_file.content_type,
    )
    return {"filename": uploaded_file.filename, "size": uploaded_file.size, "content_type": uploaded_file.content_type}

@app.post("/upload-link-youtube/")
async def upload_link_youtube(link: str):
    # Get the YouTube video transcription
    return {"link": link}