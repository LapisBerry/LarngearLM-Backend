from fastapi import FastAPI, UploadFile
import fitz # PyMuPDF
from minio import Minio

app = FastAPI()

client = Minio(
    endpoint="localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Create a bucket if it doesn't exist
bucket_name = "pdfs"
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)

@app.get("/")
def read_root():
    print(len(client.list_buckets()))
    return {"message": "Welcome to LarngearLM-Backend API"}

# POST that get PDF file from user and return some texts
@app.post("/upload-pdf/")
async def upload_pdf(uploaded_file: UploadFile):
    pdf_bytes = await uploaded_file.read() # NOT SURE!!! WHY it has to be read first
    client.put_object(
        bucket_name="pdfs",
        object_name=uploaded_file.filename,
        data=uploaded_file.file,
        length=-1,  # -1 means the length is unknown
        content_type=uploaded_file.content_type,
        part_size=10 * 1024 * 1024  # 1 MB part size
    )
    # show item in MinIO bucket
    print(client.stat_object(bucket_name, uploaded_file.filename).object_name)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texts = '\n'.join(page.get_text() for page in doc)
    return {"filename": uploaded_file.filename, "content_type": uploaded_file.content_type, "size": len(texts), "texts": texts}

@app.post("/upload-link-youtube/")
async def upload_link_youtube(link: str):
    # Get the YouTube video transcription
    
    return {"link": link}