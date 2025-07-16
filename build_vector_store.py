from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import chromadb

# Load PDFs from folder
loader = DirectoryLoader(
    path='examples/',
    glob="**/*.pdf",
    loader_cls=PyPDFLoader
)

docs = loader.load()  # Each doc has .page_content and .metadata["source"]

for doc in docs:
    doc.metadata["object_name"] = "test_object_name"

# Split into chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents = text_splitter.split_documents(docs)

# Store in Chroma with metadata
embedding = OllamaEmbeddings(model="nomic-embed-text")

chroma_client = chromadb.HttpClient(host="localhost", port=8000)

vector_store = Chroma(
    client=chroma_client,
    collection_name="my_collection",
    embedding_function=embedding
)

vector_store.add_documents(documents);
