"""Main FastAPI server entrypoint for Talem AI."""

import asyncio
import json
from os import getenv
from datetime import datetime
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from bson import ObjectId
from bson.errors import InvalidId
from bson.json_util import dumps
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_astradb import AstraDBVectorStore
from langchain_cohere import CohereEmbeddings

from decorators import precheck
from helper.auth import create_session, destroy_session, get_session_email
from helper.cookie import create_cookie, destroy_cookie
from helper.ai import query_model
from helper.mongodb import get_mongo_client

load_dotenv()

ASTRA_DB_API_ENDPOINT = getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_NAMESPACE = getenv("ASTRA_DB_NAMESPACE")
COHERE_API_KEY = getenv("COHERE_API_KEY")

executor = ThreadPoolExecutor(max_workers=2)


def extract_document_content(doc):
    """Safely extract content from various document formats."""
    try:
        if hasattr(doc, "page_content"):
            return doc.page_content
        if hasattr(doc, "content"):
            return doc.content
        if isinstance(doc, dict):
            return doc.get("page_content") or doc.get("content") or ""
        return str(doc)
    except AttributeError as e:
        print(f"Error extracting content from doc: {e}")
        return ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize embeddings and vectorstore at server startup."""
    print("=== SERVER STARTUP ===")
    try:
        print("🔄 Initializing Cohere embeddings...")
        app.state.embeddings = CohereEmbeddings(
            model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY
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
    except (ValueError, RuntimeError) as e:
        print(f"❌ Startup failed: {e}")
        raise
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai.talem.org", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
@precheck.decorator
async def handle_index_request(_request: Request):
    """Basic health check response."""
    return {"response": "Talem AI server"}


@app.post("/chat/")
@precheck.decorator
async def handle_chat_request(request: Request):
    """Process user query and return response from the language model."""
    response_data = None
    error_response = None

    try:
        data = await request.json()
        query = data.get("query")
        if not query:
            return {"error": "Query missing"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

    if not (hasattr(app.state, "embeddings") and hasattr(app.state, "vectorstore")):
        return {"error": "Server still initializing, please try again shortly"}

    try:
        retriever = app.state.vectorstore.as_retriever()
        loop = asyncio.get_running_loop()
        retrieved_docs = await loop.run_in_executor(executor, retriever.invoke, query)

        context_parts = [
            extract_document_content(doc).strip()
            for doc in retrieved_docs
            if extract_document_content(doc).strip()
        ]

        if not context_parts:
            return {"error": "No relevant content found"}

        context = "\n\n".join(context_parts)
    except RuntimeError as exc:
        print(f"Retrieval error: {exc}")
        return {"error": f"Retrieval failed: {exc}"}

    try:
        response = await query_model(context, query)
        response_data = {"response": response}
    except RuntimeError as exc:
        print(f"Model inference error: {exc}")
        return {"error": f"Model inference failed: {exc}"}

    return response_data


@app.post("/login/")
async def handle_login_request(request: Request):
    """Validate token, create session and set cookie."""
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

    token = data.get("token")
    if not token:
        return {"error": "Token missing"}

    session_id = create_session(token)
    if session_id:
        return create_cookie(session_id)
    return {"response": "Error in logging process. Try again."}


@app.post("/logout/")
async def handle_logout_request(request: Request):
    """Destroy session cookie on logout."""
    success = await destroy_session(request)
    if success:
        return destroy_cookie()
    return {"response": "Error in logging out process. Try again."}


@app.get("/chat-history/")
@precheck.decorator
async def handle_chat_history_request(request: Request):
    """Fetch saved chat history for the authenticated user."""
    email = await get_session_email(request)
    client = get_mongo_client()
    collection = client["chat_database"]["chat_history"]
    chat_history = list(collection.find({"email": email}))
    return JSONResponse(content=json.loads(dumps({"response": chat_history})))


@app.post("/chat-history/")
@precheck.decorator
async def handle_save_chat_message(request: Request):
    """Save a chat exchange to the database."""
    data = await request.json()
    messages = data.get("messages")
    email = await get_session_email(request)
    client = get_mongo_client()
    collection = client["chat_database"]["chat_history"]
    chat_document = {"email": email, "messages": messages, "timestamp": datetime.utcnow()}
    result = collection.insert_one(chat_document)
    saved_doc = collection.find_one({"_id": result.inserted_id})
    return JSONResponse(content=json.loads(dumps({"response": saved_doc})))


@app.delete("/chat-history/")
@precheck.decorator
async def handle_delete_single_chat_history(request: Request):
    """Delete a single chat history entry by ID."""
    data = await request.json()
    chat_id = data.get("chat_id")
    email = await get_session_email(request)
    client = get_mongo_client()
    collection = client["chat_database"]["chat_history"]

    try:
        oid = ObjectId(chat_id)
    except InvalidId as exc:
        return JSONResponse(content={"error": f"Invalid chat_id: {exc}"}, status_code=400)

    result = collection.delete_one({"_id": oid, "email": email})

    if result.deleted_count == 1:
        return JSONResponse(content={"response": f"Deleted chat message with id {chat_id}."})

    return JSONResponse(
        content={"error": "Chat message not found or not authorized."}, status_code=404
    )
