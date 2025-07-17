import chromadb
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

chroma_client = chromadb.HttpClient(host="localhost", port=8000)
embedding = OllamaEmbeddings(model="nomic-embed-text")

vector_store = Chroma(
    client=chroma_client,
    collection_name="my_collection",
    embedding_function=embedding
)

retriever = vector_store.as_retriever()
