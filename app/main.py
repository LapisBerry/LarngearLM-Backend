from fastapi import FastAPI, UploadFile
import fitz # PyMuPDF

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to LarngearLM-Backend API"}

# POST that get PDF file from user and return some texts
@app.post("/upload-pdf/")
async def upload_pdf(uploaded_file: UploadFile):
    pdf_bytes = await uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texts = '\n'.join(page.get_text() for page in doc)
    print(texts)
    return {"filename": uploaded_file.filename, "content_type": uploaded_file.content_type, "size": len(texts), "texts": texts}
