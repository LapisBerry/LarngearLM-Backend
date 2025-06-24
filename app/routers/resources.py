from datetime import timedelta
import uuid
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from bs4 import BeautifulSoup
import re
from app.database import get_db
from app.model import FileMetadata
from app.utils.minio_client import client, bucket_name

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
                "content_type": file.content_type,
                "size": file.size,
                "last_modified": file.created_at.isoformat(),
            }
        )
    return {"files": files}


@router.post("/")
async def upload_resource(
    uploaded_file: UploadFile = File(...), db: Session = Depends(get_db)
):
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


@router.post("/youtube-transcript/")
async def create_youtube_transcript(video_url: str, db: Session = Depends(get_db)):
    try:
        yt = YouTube(video_url)
        video_id = yt.video_id
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        content = "\n".join([f"{item['start']} - {item['text']}" for item in transcript]).encode("utf-8")
        print(content)
        filename = f"{video_id}_transcript.txt"
        object_name = str(uuid.uuid4()) + "_" + filename

        # Save the transcript to MinIO
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=BytesIO(content),
            length=len(content),
            content_type="text/plain; charset=utf-8",
        )

        # Save metadata to the database
        file_metadata = FileMetadata(
            filename=filename,
            bucket_name=bucket_name,
            object_name=object_name,
            content_type="text/plain",
            size=len(content),
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)

        return {
            "message": "YouTube transcript created successfully.",
            "filename": filename,
            "size": len(content),
            "content_type": "text/plain",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/website-text")
async def create_website_text(url: str, db: Session = Depends(get_db)):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch the website content.")

        # Scrape the text from website
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.title.string if soup.title else url
        filename = f"{title}_website_content.txt"
        text = soup.get_text()
        content = text.encode("utf-8")

        # Remove duplicate newlines
        content = re.sub(r'\n+', '\n\n', text).encode("utf-8")

        object_name = str(uuid.uuid4()) + "_" + filename

        # Save the website content to MinIO
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=BytesIO(content),
            length=len(content),
            content_type="text/plain; charset=utf-8",
        )

        # Save metadata to the database
        file_metadata = FileMetadata(
            filename=filename,
            bucket_name=bucket_name,
            object_name=object_name,
            content_type="text/plain",
            size=len(content),
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)

        return {
            "message": "Website text created successfully.",
            "filename": filename,
            "size": len(content),
            "content_type": "text/plain",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{fileId}")
async def delete_resource(fileId: int, db: Session = Depends(get_db)):
    try:
        # search id in the database
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == fileId).first()
        if not file_metadata:
            raise HTTPException(
                status_code=404, detail="File not found in the database."
            )

        filename = file_metadata.filename
        client.remove_object(
            bucket_name=bucket_name, object_name=file_metadata.object_name
        )

        db.delete(file_metadata)
        db.commit()

        return {"message": f"Resource {fileId}: {filename} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
