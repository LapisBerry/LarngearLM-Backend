from fastapi import APIRouter
import os
from dotenv import load_dotenv
import requests
from app.utils.chroma_client import retriever

load_dotenv()

router = APIRouter()


@router.get("/article/{article_id}")
async def getArticleById(article_id: str):
    access_token = signin(os.getenv("USERNAME"), os.getenv("PASSWORD"))["data"][
        "accessToken"
    ]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{os.getenv('LMS_API_URL')}/article-admin/articles/{article_id}",
        headers=headers,
    )
    return response.json()


@router.get("/asset-stores/bundle/{bundleName}/{refkey}")
async def getAssetStoreBundle(bundleName: str, refkey: str):
    access_token = signin(os.getenv("USERNAME"), os.getenv("PASSWORD"))["data"][
        "accessToken"
    ]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{os.getenv('LMS_API_URL')}/asset-stores/bundle/{bundleName}/{refkey}",
        headers=headers,
    )
    return response.json()


@router.post("/search")
async def queryResources(query: str):
    results = retriever.invoke(query)
    return {"results": results}


# Login to LMS and initialize access token
def signin(username, password):
    url = f"{os.getenv("LMS_API_URL")}/auth/signin"
    payload = {"username": username, "password": password, "rememberMe": True}
    response = requests.post(url, json=payload)
    return response.json()
