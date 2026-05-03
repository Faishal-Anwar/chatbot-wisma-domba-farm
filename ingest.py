import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

DATA_DIR = "data"
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

def ingest_data():
    if not PINECONE_API_KEY:
        print("Error: PINECONE_API_KEY not found in .env")
        return

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Create index if it doesn't exist
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=768, # Dimension for models/gemini-embedding-001
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    # Load documents
    documents = []
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".txt"):
                file_path = os.path.join(DATA_DIR, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    documents.append(Document(page_content=content, metadata={"source": filename}))

    if not documents:
        print("No documents found to ingest.")
        return

    # Initialize Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="retrieval_document"
    )

    # Ingest to Pinecone
    print(f"Ingesting {len(documents)} documents to Pinecone...")
    PineconeVectorStore.from_documents(
        documents, 
        embeddings, 
        index_name=INDEX_NAME
    )
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_data()
