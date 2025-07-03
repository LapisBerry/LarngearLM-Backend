from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import fitz
import requests
import json
from app.utils.minio_client import client, bucket_name
from app.database import get_db
from app.model import FileMetadata

router = APIRouter()


@router.post("/")
async def give_instruction(
    instruction: str,
    selected_files: list[int] = [],
    stream: bool = False,
    db: Session = Depends(get_db),
):
    try:
        instructionAndResource = get_instruction_and_resources(
            instruction,
            selected_files,
            db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1",
            "prompt": instructionAndResource,
            "stream": stream,
        },
        stream=stream,
    )
    if stream:

        def event_generator():
            for chunk in response.iter_lines():
                yield chunk

        return StreamingResponse(event_generator(), media_type="text/plain")
    else:
        return response.json()


def get_instruction_and_resources(
    instruction: str,
    selected_files: list[int],
    db: Session,
):
    instructionAndResource = instruction + "\n\n"
    if len(selected_files) > 0:
        instructionAndResource += "Resources:\n"
        for fileId in selected_files:
            file_metadata = (
                db.query(FileMetadata).filter(FileMetadata.id == fileId).first()
            )
            if not file_metadata:
                raise HTTPException(
                    status_code=404, detail=f"File with ID {fileId} not found."
                )

            instructionAndResource += (
                f"***\n{file_metadata.filename}\n***\n\n<STARTFILE>\n"
            )
            object_name = file_metadata.object_name

            # Fetch the file from MinIO
            file = client.get_object(bucket_name=bucket_name, object_name=object_name)

            if file_metadata.content_type == "application/pdf":
                instructionAndResource += process_pdf(file)
            elif file_metadata.content_type == "text/plain":
                instructionAndResource += process_text(file)
            instructionAndResource += "<ENDFILE>\n"
            file.close()

    return instructionAndResource


def process_pdf(file):
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in pdf_document:
        text += page.get_text()
    return text


def process_text(file):
    return file.read().decode("utf-8")


@router.post("/article/")
async def create_article():
    try:
        prompt = """
        Create a random article then answer only in the JSON format:
        {
            "title": "<title>",
            "tags": ["<tag1>", "<tag2>"],
            "expectedDuration": "<duration expected to read the article in iso 8601 format>",
            "content": "<content>"
        }
        """
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1",
                "prompt": prompt,
                "stream": False,
            },
        )
        # the response have prop "response" which is a json string, Get it in json format
        response = response.json()
        response = json.loads(response["response"])
        print(response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
