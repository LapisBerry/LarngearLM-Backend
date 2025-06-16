from fastapi import APIRouter, HTTPException
from app.utils.minio_client import client, bucket_name
import fitz
import requests

router = APIRouter()

@router.post("/")
async def give_instruction(instruction: str, selected_files: list[str] = []):
    instructionAndResource = instruction + "\n\n"
    if len(selected_files) > 0:
        instructionAndResource += "Resources:\n"
        for filename in selected_files:
            instructionAndResource += f"***\n{filename}\n***\n\n<STARTFILE>\n"
            try:
                file = client.get_object(bucket_name=bucket_name, object_name=filename)
                pdf_document = fitz.open(stream=file.read(), filetype="pdf")
                for page in pdf_document:
                    instructionAndResource += page.get_text()
                instructionAndResource += "<ENDFILE>\n"
                file.close()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing file {filename}: {str(e)}")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1",
            "prompt": instructionAndResource,
            "stream": False
        }
    )
    return response.json()
