from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

embedding = OllamaEmbeddings(model="nomic-embed-text")

db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding
)

retriever = db.as_retriever()

query = "treasure?"

results = retriever.invoke(query)

for res in results:
    print("##########")
    print(res.page_content)
    print(res.metadata)  # Metadata includes source, etc.
