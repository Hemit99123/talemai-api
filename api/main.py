"""Clean FastAPI server with Cohere embeddings - reliable alternative."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_astradb import AstraDBVectorStore
from langchain_cohere import CohereEmbeddings
from pydantic import BaseModel
from helper.auth import create_session, destroy_session, get_session_email
from helper.cookie import create_cookie, destroy_cookie 
from decorators import precheck
from helper.ai import query_model
from dotenv import load_dotenv
from os import getenv
from helper.mongodb import get_mongo_client
from datetime import datetime
from contextlib import asynccontextmanager

def extract_document_content(doc):
    """Safely extract content from various document formats."""
    try:
        # Try page_content first (most common with LangChain)
        if hasattr(doc, 'page_content'):
            return doc.page_content
        
        # Try content attribute
        if hasattr(doc, 'content'):
            return doc.content
        
        # Try dictionary access
        if isinstance(doc, dict):
            return doc.get('page_content') or doc.get('content') or ""
        
        # Try string conversion as last resort
        return str(doc)
        
    except Exception as e:
        print(f"Error extracting content from doc: {e}")
        return ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan management - clean and fast."""
    # Lifespan runs on startup of FastAPI server
    # Initialize embeddings and vectorstore here
    
    print("=== SERVER STARTUP ===")
    
    try:
        print("🔄 Initializing Cohere embeddings...")
        app.state.embeddings = CohereEmbeddings(
            model="embed-english-v3.0",
            cohere_api_key=COHERE_API_KEY
        )
        print("✅ Cohere embeddings initialized!")

        print("🔄 Initializing vectorstore...")
        app.state.vectorstore = AstraDBVectorStore(
            collection_name="main_v6",
            embedding=app.state.embeddings,
            api_endpoint=ASTRA_DB_API_ENDPOINT,
            token=ASTRA_DB_APPLICATION_TOKEN,
            namespace=ASTRA_DB_NAMESPACE,
        )
        print("✅ Vectorstore initialized!")
        print("=== INITIALIZATION COMPLETE ===")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

# Load .env config
load_dotenv()

ASTRA_DB_API_ENDPOINT = getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_NAMESPACE = getenv("ASTRA_DB_NAMESPACE")
GROQ_API_KEY = getenv("GROQ_API_KEY")
COHERE_API_KEY = getenv("COHERE_API_KEY")

# Global executor for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=2)

class QueryModal(BaseModel):
    query: str

class TokenModal(BaseModel):
    token: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai.talem.org", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
@precheck.decorator
async def handle_index_request(request: Request):
    return {"response": "Talem AI server"}

@app.post("/chat/")
@precheck.decorator
async def handle_chat_request(request: Request):
    """Handle POST request, process query, and return AI-generated response."""
    try:
        data = await request.json()
        query = data.get("query")
        if not query:
            return {"error": "Query missing"}
    except Exception:
        return {"error": "Invalid JSON"}

    if not hasattr(app.state, "embeddings") or not hasattr(app.state, "vectorstore"):
        return {"error": "Server still initializing, please try again in a moment"}

    try:
        # Use the initialized vectorstore from app.state
        retriever = app.state.vectorstore.as_retriever()
        
        # Run the synchronous retriever operation in executor
        loop = asyncio.get_event_loop()
        retrieved_docs = await loop.run_in_executor(
            executor,
            retriever.invoke,
            query
        )
        
        # Safe content extraction
        context_parts = []
        for doc in retrieved_docs:
            content = extract_document_content(doc)
            if content and content.strip():
                context_parts.append(content.strip())
        
        context = "\n\n".join(context_parts)
        
        if not context:
            return {"error": "No relevant content found"}
            
    except Exception as e:
        print(f"Retrieval error details: {e}")
        return {"error": f"Retrieval failed: {str(e)}"}

    try:
        # Call query_model directly since it's async
        response = await query_model(context, query)
    except Exception as e:
        print(f"Model inference error: {e}")
        return {"error": f"Model inference failed: {str(e)}"}

    return {"response": response}

@app.post("/login/")
async def handle_login_request(request: Request):
    data = await request.json()
    token = data.get("token")
    session_id = create_session(token)
    if session_id:
        return create_cookie(session_id)
    return {"response": "Error in logging process. Try again."}

@app.post("/logout/")
async def handle_logout_request(request: Request):
    if destroy_session(request):
        return destroy_cookie()
    return {"response": "Error in logging out process. Try again."}

@app.get("/chat-history/")
@precheck.decorator
async def handle_chat_history_request(request: Request):
    email = await get_session_email(request)
    client = get_mongo_client()
    collection = client['chat_database']['chat_history']
    chat_history = list(collection.find({"email": email}))
    return {"response": chat_history}

@app.post("/chat-history/")
@precheck.decorator
async def handle_save_chat_message(request: Request):
    data = await request.json()
    messages = data.get("messages")
    email = await get_session_email(request)


    client = get_mongo_client()
    collection = client['chat_database']['chat_history']
    chat_document = {
        "email": email,
        "messages": messages,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(chat_document)
    return {"response": chat_document}

@app.delete("/chat-history/")
@precheck.decorator
async def handle_delete_chat_history(request: Request):
    email = get_session_email(request)

    client = get_mongo_client()
    collection = client['chat_database']['chat_history']
    result = collection.delete_many({"email": email})
    return {"response": f"Deleted {result.deleted_count} chat messages."}