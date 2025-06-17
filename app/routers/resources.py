from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.minio_client import client, bucket_name
from datetime import timedelta

router = APIRouter()

@router.get("/")
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

@router.post("/")
async def upload_resource(uploaded_file: UploadFile = File(...)):
    client.put_object(
        bucket_name=bucket_name,
        object_name=uploaded_file.filename,
        data=uploaded_file.file,
        length=uploaded_file.size,
        content_type=uploaded_file.content_type,
    )
    return {"filename": uploaded_file.filename, "size": uploaded_file.size, "content_type": uploaded_file.content_type}

@router.delete("/{filename}")
async def delete_resource(filename: str):
    try:
        client.remove_object(bucket_name=bucket_name, object_name=filename)
        return {"message": f"Resource {filename} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
