import os
from dotenv import load_dotenv
import chromadb
import bs4
import requests
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
)
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Load environment variables
load_dotenv()

# Initialize embedding and Chroma client
embedding = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chroma_client = chromadb.HttpClient(host="localhost", port=8001)
vector_store = Chroma(
    client=chroma_client, collection_name="my_collection", embedding_function=embedding
)


# Login to LMS and initialize access token
def signin(username, password):
    url = f"{os.getenv("LMS_API_URL")}/auth/signin"
    payload = {"username": username, "password": password, "rememberMe": True}
    response = requests.post(url, json=payload)
    return response.json()


access_token = signin(os.getenv("USERNAME_LMS"), os.getenv("PASSWORD_LMS"))["data"][
    "accessToken"
]


# Functions to interact with LMS API
def getArticleAdmin():
    url = f"{os.getenv("LMS_API_URL")}/article-admin/articles"
    headers = {"Authorization": f"Bearer {access_token}", "accept": "application/json"}
    response = requests.get(
        url, headers=headers, params={"pageSize": 60, "current": 1, "filter": {}}
    )
    return response.json()


def getDatastoreAdmin():
    url = f"{os.getenv("LMS_API_URL")}/datastore-admin/datastores"
    headers = {"Authorization": f"Bearer {access_token}", "accept": "application/json"}
    response = requests.get(
        url, headers=headers, params={"pageSize": 60, "current": 1, "filter": {}}
    )
    return response.json()


def getDatastoreAdminSectionById(datastoreId: str):
    url = f"{os.getenv("LMS_API_URL")}/datastore-admin/datastores/{datastoreId}/sections"
    headers = {"Authorization": f"Bearer {access_token}", "accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()


def getAssetStoresBundleData(bundleName: str, refKey: str):
    url = f"{os.getenv("LMS_API_URL")}/asset-stores/bundle/{bundleName}/{refKey}"
    headers = {"Authorization": f"Bearer {access_token}", "accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()


# Load articles from LMS
articles = getArticleAdmin()["data"]

docs = []
for article in articles:
    if not article["contentHtml"]:
        print(f"Skipping article {article["id"]} due to missing content.")
        continue
    content_html = article["contentHtml"]
    soup = bs4.BeautifulSoup(content_html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    doc = Document(
        page_content=text,
        metadata={
            "id": article["id"],
            "mimeType": "text/plain",
            "code": article["code"],
            "name": article["name"],
        },
    )
    docs.append(doc)

documents = text_splitter.split_documents(docs)
vector_store.add_documents(documents)


# # Download all datastore pdfs
datastores = getDatastoreAdmin()["data"]

for datastore in datastores:
    sections = getDatastoreAdminSectionById(datastore["id"])["data"]
    for section in sections:
        for datastoreUnit in section["datastoreUnits"]:
            if datastoreUnit["type"] == "pdf":
                assetStore = datastoreUnit["assetStore"]
                url = getAssetStoresBundleData(
                    assetStore["bundleName"], assetStore["refKey"]
                )["data"]
                # Download the pdf file
                pdf_response = requests.get(url)
                if pdf_response.status_code == 200:
                    # Save the PDF to a temporary file
                    pdf_path = f"temp_{datastoreUnit["id"]}.pdf"
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_response.content)

                    # Load the PDF using PyPDFLoader
                    loader = PyPDFLoader(pdf_path)
                    docs = loader.load()

                    # Split the documents into chunks
                    documents = text_splitter.split_documents(docs)

                    # Add metadata to each document
                    for doc in documents:
                        doc.metadata["name"] = datastoreUnit["name"]
                        doc.metadata["mimeType"] = "application/pdf"
                        doc.metadata["bundleName"] = assetStore["bundleName"]
                        doc.metadata["refKey"] = assetStore["refKey"]
                    
                    if len(documents) == 0:
                        print(f"No documents found in {pdf_path}, skipping.")
                        os.remove(pdf_path)  # Clean up the temporary file
                        continue
                    vector_store.add_documents(documents)
                    os.remove(pdf_path)  # Clean up the temporary file
