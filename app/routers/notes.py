from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import uuid
from sqlalchemy.orm import Session
from datetime import timedelta
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
        notes.append({
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
        })
    return {"notes": notes}

@router.get("/{note_id}")
async def get_put_presigned_url(note_id: int, db: Session = Depends(get_db)):
    note = db.query(NoteMetadata).filter(NoteMetadata.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return {
        "id": note.id,
        "title": note.title,
        "url_put": client.get_presigned_url(
            method="PUT",
            bucket_name=note.bucket_name,
            object_name=note.object_name,
            expires=timedelta(minutes=10),
        ),
    }

@router.post("/")
async def upload_note(
    title: str, uploaded_file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        object_name = str(uuid.uuid4()) + "_" + uploaded_file.filename

        client.put_object(
            bucket_name=NOTE_BUCKET_NAME,
            object_name=object_name,
            data=uploaded_file.file,
            length=uploaded_file.size,
            content_type=uploaded_file.content_type,
        )

        # Save metadata to the database
        note_metadata = NoteMetadata(
            title=title,
            bucket_name=NOTE_BUCKET_NAME,
            object_name=object_name,
            content_type=uploaded_file.content_type,
            size=uploaded_file.size,
        )
        db.add(note_metadata)
        db.commit()
        db.refresh(note_metadata)

        return {"message": "Note uploaded successfully", "note_id": note_metadata.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
