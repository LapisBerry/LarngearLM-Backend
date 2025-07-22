from fastapi import APIRouter, HTTPException, Depends
from starlette.datastructures import UploadFile
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import requests
import io
from bs4 import BeautifulSoup
from app.database import get_db
from app.routers.resources import upload_resource
from app.utils.chroma_client import retriever

load_dotenv()

router = APIRouter()


@router.get("/article/{article_id}")
async def getArticleById(article_id: str):
    access_token = signin(os.getenv("USERNAME_LMS"), os.getenv("PASSWORD_LMS"))["data"][
        "accessToken"
    ]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{os.getenv('LMS_API_URL')}/article-admin/articles/{article_id}",
        headers=headers,
    )
    return response.json()


@router.get("/asset-stores/bundle/{bundleName}/{refKey}")
async def getAssetStoreBundle(bundleName: str, refKey: str):
    access_token = signin(os.getenv("USERNAME_LMS"), os.getenv("PASSWORD_LMS"))["data"][
        "accessToken"
    ]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{os.getenv('LMS_API_URL')}/asset-stores/bundle/{bundleName}/{refKey}",
        headers=headers,
    )
    return response.json()


@router.post("/search")
async def queryResources(query: str):
    results = retriever.invoke(query)
    return {"results": results}


@router.post("/use-lms-resource")
async def useLmsResource(type: int, fileName: str, articleId: str = None, bundleName: str = None, refKey: str = None, db: Session = Depends(get_db)):
    if type == 0 and articleId:
        response = await getArticleById(articleId)
        content_html = response["data"]["contentHtml"]
        soup = BeautifulSoup(content_html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        content_bytes = text.encode("utf-8")
        byteio_content = io.BytesIO(content_bytes)
        headers = {"content-type": "text/plain; charset=utf-8"}
        uploaded_file = UploadFile(filename=fileName, file=byteio_content, size=len(content_bytes), headers=headers)
        return await upload_resource(uploaded_file=uploaded_file, db=db)
    elif type == 1 and bundleName and refKey:
        response = await getAssetStoreBundle(bundleName, refKey)
        pdfUrl = response["data"]
        content = requests.get(pdfUrl).content
        file = io.BytesIO(content)
        headers = {"content-type": "application/pdf"}
        uploaded_file = UploadFile(filename=fileName, file=file, size=len(content), headers=headers)
        return await upload_resource(uploaded_file=uploaded_file, db=db)
    raise HTTPException(status_code=400, detail="Invalid parameters provided.")

# Login to LMS and initialize access token
def signin(username, password):
    url = f"{os.getenv("LMS_API_URL")}/auth/signin"
    payload = {"username": username, "password": password, "rememberMe": True}
    response = requests.post(url, json=payload)
    return response.json()
