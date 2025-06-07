from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Minio(
    endpoint="localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)
bucket_name = "pdfs"
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name=bucket_name)

@app.get("/")
def read_root():
    return {"message": "Welcome to LarngearLM-Backend API"}

@app.get("/get-resources/")
async def get_resources():
    files = []
    for obj in client.list_objects(bucket_name=bucket_name, recursive=True):
        files.append({
            "filename": obj.object_name,
            "size": obj.size,
            "last_modified": obj.last_modified.isoformat(),
            "content_type": "application/pdf"
        })
    return {"files": files}

@app.get("/get-resource/{filename}")
async def get_resource(filename: str):
    try:
        file_data = client.get_object(bucket_name=bucket_name, object_name=filename)
        return StreamingResponse(file_data, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename={filename}"})
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload-resource/")
async def upload_resource(uploaded_file: UploadFile = File(...)):
    client.put_object(
        bucket_name=bucket_name,
        object_name=uploaded_file.filename,
        data=uploaded_file.file,
        length=uploaded_file.size,
        content_type=uploaded_file.content_type,
    )
    return {"filename": uploaded_file.filename, "size": uploaded_file.size, "content_type": uploaded_file.content_type}

@app.delete("/delete-resource/{filename}")
async def delete_resource(filename: str):
    client.remove_object(bucket_name=bucket_name, object_name=filename)
    return {"message": f"Resource {filename} deleted successfully."}
