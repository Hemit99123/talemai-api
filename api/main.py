"""Clean FastAPI server with Cohere embeddings - reliable alternative."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from bson.json_util import dumps
import json
from bson import ObjectId

def extract_document_content(doc):
    """Safely extract content from various document formats."""
    try:
        if hasattr(doc, 'page_content'):
            return doc.page_content
        if hasattr(doc, 'content'):
            return doc.content
        if isinstance(doc, dict):
            return doc.get('page_content') or doc.get('content') or ""
        return str(doc)
    except Exception as e:
        print(f"Error extracting content from doc: {e}")
        return ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan management - clean and fast."""
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
COHERE_API_KEY = getenv("COHERE_API_KEY")


# CPU execution 
executor = ThreadPoolExecutor(max_workers=2)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai.talem.org", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS", "DELETE"],
    allow_headers=["*"],
)

@app.get("/")
@precheck.decorator
async def handle_index_request(request: Request):
    return {"response": "Talem AI server"}

@app.post("/chat/")
@precheck.decorator
async def handle_chat_request(request: Request):
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
        retriever = app.state.vectorstore.as_retriever()
        loop = asyncio.get_event_loop()
        retrieved_docs = await loop.run_in_executor(
            executor,
            retriever.invoke,
            query
        )

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
    return JSONResponse(content=json.loads(dumps({"response": chat_history})))

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
    result = collection.insert_one(chat_document)
    saved_doc = collection.find_one({"_id": result.inserted_id})
    return JSONResponse(content=json.loads(dumps({"response": saved_doc})))

@app.delete("/chat-history/")
@precheck.decorator
async def handle_delete_single_chat_history(request: Request):
    data = await request.json()
    chat_id = data.get("chat_id")

    email = await get_session_email(request)
    client = get_mongo_client()
    collection = client['chat_database']['chat_history']
    try:
        result = collection.delete_one({"_id": ObjectId(chat_id), "email": email})
        if result.deleted_count == 1:
            return JSONResponse(content={"response": f"Deleted chat message with id {chat_id}."})
        else:
            return JSONResponse(content={"error": "Chat message not found or not authorized."}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"error": f"Invalid chat_id: {str(e)}"}, status_code=400)
