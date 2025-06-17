from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.utils.minio_client import client, bucket_name
from datetime import timedelta
import uuid
from app.database import get_db
from sqlalchemy.orm import Session
from app.model import FileMetadata

router = APIRouter()


@router.get("/")
async def get_resources(db: Session = Depends(get_db)):
    files = []
    # Fetch file metadata from the database
    file_metadata = db.query(FileMetadata).all()
    for file in file_metadata:
        files.append(
            {
                "id": file.id,
                "filename": file.filename,
                "bucket_name": file.bucket_name,
                "url": client.get_presigned_url(
                    method="GET",
                    bucket_name=file.bucket_name,
                    object_name=file.object_name,
                    expires=timedelta(minutes=60),
                ),
                "size": file.size,
                "last_modified": file.created_at.isoformat(),
            }
        )
    return {"files": files}


@router.post("/")
async def upload_resource(uploaded_file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        object_name = str(uuid.uuid4()) + "_" + uploaded_file.filename

        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=uploaded_file.file,
            length=uploaded_file.size,
            content_type=uploaded_file.content_type,
        )

        # Save metadata to the database
        file_metadata = FileMetadata(
            filename=uploaded_file.filename,
            bucket_name=bucket_name,
            object_name=object_name,
            content_type=uploaded_file.content_type,
            size=uploaded_file.size,
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)

        return {
            "message": "Resource uploaded successfully.",
            "filename": uploaded_file.filename,
            "size": uploaded_file.size,
            "content_type": uploaded_file.content_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{fileId}")
async def delete_resource(fileId: int, db: Session = Depends(get_db)):
    try:
        # search id in the database
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == fileId).first()
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found in the database.")
        
        filename = file_metadata.filename
        client.remove_object(bucket_name=bucket_name, object_name=file_metadata.object_name)

        db.delete(file_metadata)
        db.commit()

        return {"message": f"Resource {fileId}: {filename} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
