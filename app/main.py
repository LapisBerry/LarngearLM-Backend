from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio
import requests
from datetime import timedelta
import fitz

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
bucket_name = "files"
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
            "url": client.get_presigned_url(
                method="GET",
                bucket_name=bucket_name,
                object_name=obj.object_name,
                expires=timedelta(minutes=60)
            ),
            "size": obj.size,
            "last_modified": obj.last_modified.isoformat()
        })
    return {"files": files}

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

@app.post("/give-instruction/")
async def give_instruction(instruction: str, selected_files: list[str] = []):
    instructionAndResource = instruction + "\n\n"
    if len(selected_files) > 0:
        instructionAndResource += "Resources:\n"
        for filename in selected_files:
            instructionAndResource += f"***\n"
            instructionAndResource += f"{filename}\n"
            instructionAndResource += f"***\n"
            instructionAndResource += f"\n<STARTFILE>\n"
            file = client.get_object(
                bucket_name=bucket_name,
                object_name=filename
            )
            pdf_document = fitz.open(stream=file.read(), filetype="pdf")
            for page in pdf_document:
                instructionAndResource += page.get_text()
            instructionAndResource += "<ENDFILE>\n"
            file.close()
    print(instructionAndResource)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1",
            "prompt": instructionAndResource,
            "stream": False
        }
    )
    return response.json()

@app.delete("/delete-resource/{filename}")
async def delete_resource(filename: str):
    client.remove_object(bucket_name=bucket_name, object_name=filename)
    return {"message": f"Resource {filename} deleted successfully."}
