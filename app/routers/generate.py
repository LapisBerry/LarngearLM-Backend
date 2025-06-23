from fastapi import APIRouter, HTTPException, Depends
from app.utils.minio_client import client, bucket_name
import fitz
import requests
from app.database import get_db
from sqlalchemy.orm import Session
from app.model import FileMetadata

router = APIRouter()

@router.post("/")
async def give_instruction(instruction: str, selected_files: list[int] = [], db: Session = Depends(get_db)):
    instructionAndResource = instruction + "\n\n"
    if len(selected_files) > 0:
        instructionAndResource += "Resources:\n"
        for fileId in selected_files:
            instructionAndResource += f"***\n{fileId}\n***\n\n<STARTFILE>\n"
            try:
                # Get the object name from Database using fileId
                file_metadata = db.query(FileMetadata).filter(FileMetadata.id == fileId).first()
                if not file_metadata:
                    raise HTTPException(status_code=404, detail=f"File with ID {fileId} not found.")
                object_name = file_metadata.object_name

                # Fetch the file from MinIO
                file = client.get_object(bucket_name=bucket_name, object_name=object_name)
                pdf_document = fitz.open(stream=file.read(), filetype="pdf")
                for page in pdf_document:
                    instructionAndResource += page.get_text()
                instructionAndResource += "<ENDFILE>\n"
                file.close()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing file {fileId}: {str(e)}")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1",
            "prompt": instructionAndResource,
            "stream": False
        }
    )
    return response.json()
