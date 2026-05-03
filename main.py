import os
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain_classic.chains import RetrievalQA

# Load environment variables
load_dotenv()

# Security Configuration
API_KEY_NAME = "X-Chatbot-Key"
API_KEY = os.getenv("CHATBOT_API_KEY")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(header_value: str = Depends(api_key_header)):
    if not API_KEY: # Jika API_KEY tidak diset di server, akses diizinkan (untuk testing)
        return header_value
    if header_value == API_KEY:
        return header_value
    raise HTTPException(status_code=403, detail="Akses ditolak: API Key tidak valid")

app = FastAPI()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def setup_rag():
    google_api_key = os.getenv("GOOGLE_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")

    if not google_api_key or not pinecone_api_key or not index_name:
        print("WARNING: Missing required environment variables (GOOGLE_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME).")
        return None

    # Initialize Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="retrieval_query"
    )
    
    # Initialize Pinecone Vector Store
    vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        pinecone_api_key=pinecone_api_key
    )
    
    # Setup LLM and QA chain
    llm = ChatGoogleGenerativeAI(model="models/gemini-3-flash-preview", temperature=0.3)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    return qa_chain

# Global variable for the chain
_qa_chain = None

def get_qa_chain():
    global _qa_chain
    try:
        if _qa_chain is None:
            _qa_chain = setup_rag()
        return _qa_chain
    except Exception as e:
        print(f"FAILED TO INITIALIZE RAG: {e}")
        return None

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"message": "Wisma Domba Farm RAG API (Pinecone) is running"}

@app.post("/api/ask")
async def ask_question(request: QuestionRequest, api_key: str = Depends(get_api_key)):
    chain = get_qa_chain()
    if chain is None:
        raise HTTPException(
            status_code=500, 
            detail="RAG system not initialized. Check server logs for details."
        )
    
    try:
        response = chain.invoke({"query": request.question})
        return {"answer": response["result"]}
    except Exception as e:
        print(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
