from fastapi import APIRouter, Depends, HTTPException
import uuid
from sqlalchemy.orm import Session
from datetime import timedelta
import requests
from io import BytesIO
from app.utils.minio_client import client, NOTE_BUCKET_NAME
from app.database import get_db
from app.model import NoteMetadata

router = APIRouter()


@router.get("/")
async def get_notes(db: Session = Depends(get_db)):
    notes = []
    # Fetch note metadata from the database
    notes_metadata = db.query(NoteMetadata).all()
    for note in notes_metadata:
        notes.append(
            {
                "id": note.id,
                "title": note.title,
                "bucket_name": note.bucket_name,
                "url": client.get_presigned_url(
                    method="GET",
                    bucket_name=note.bucket_name,
                    object_name=note.object_name,
                    expires=timedelta(minutes=60),
                ),
                "content_type": note.content_type,
                "size": note.size,
                "created_at": note.created_at.isoformat(),
            }
        )
    return {"notes": notes}


@router.post("/")
async def upload_note(title: str, content: str, db: Session = Depends(get_db)):
    try:
        object_name = str(uuid.uuid4()) + "_" + title + ".txt"
        content_bytes = content.encode("utf-8")
        byteio_content = BytesIO(content_bytes)

        client.put_object(
            bucket_name=NOTE_BUCKET_NAME,
            object_name=object_name,
            data=byteio_content,
            length=len(content_bytes),
            content_type="text/plain; charset=utf-8",
        )

        # Save metadata to the database
        note_metadata = NoteMetadata(
            title=title,
            bucket_name=NOTE_BUCKET_NAME,
            object_name=object_name,
            content_type="text/plain",
            size=len(content_bytes),
        )
        db.add(note_metadata)
        db.commit()
        db.refresh(note_metadata)

        return {"message": "Note uploaded successfully", "note_id": note_metadata.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{note_id}")
async def update_note(
    note_id: int,
    title: str,
    content: str,
    db: Session = Depends(get_db),
):
    note = db.query(NoteMetadata).filter(NoteMetadata.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    put_presigned_url = client.get_presigned_url(
        method="PUT",
        bucket_name=note.bucket_name,
        object_name=note.object_name,
        expires=timedelta(minutes=10),
    )

    requests.put(
        url=put_presigned_url,
        data=content.encode("utf-8"),
        headers={
            "Content-Type": note.content_type
            + "; charset=utf-8"  # ; charset=utf-8 to ensure proper encoding for minio
        },
    )

    note.title = title
    db.commit()
    db.refresh(note)

    return {"message": "Note updated successfully", "note_id": note.id}


@router.delete("/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(NoteMetadata).filter(NoteMetadata.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Delete the object from MinIO
    client.remove_object(bucket_name=note.bucket_name, object_name=note.object_name)

    # Delete metadata from the database
    db.delete(note)
    db.commit()

    return {"message": "Note deleted successfully"}
