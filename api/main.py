"""Main entry point for the Talem AI FastAPI server."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_astradb import AstraDBVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
from helper import auth
from helper import cookie 
from decorators import precheck
from helper.ai import query_model
from dotenv import load_dotenv
from os import getenv

app = FastAPI()


load_dotenv()

ASTRA_DB_API_ENDPOINT = getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_NAMESPACE = getenv("ASTRA_DB_NAMESPACE")
GROQ_API_KEY = getenv("GROQ_API_KEY")

class QueryModal(BaseModel):
    """Schema for incoming POST request with user query."""
    query: str

class TokenModal(BaseModel):
    """Schema for incoming POST request with Google token."""
    token: str

# Needed to allow cookies to be sent to frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai.talem.org", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
@precheck.decorator
async def handle_index_request(request : Request):
    """Health check route for the server."""
    return {"response": "Talem AI server"}

@app.post("/chat/")
@precheck.decorator
async def handle_chat_request(request: Request):
    """Handle POST request, process query, and return AI-generated response."""

    data = await request.json()
    query = data.get("query")

    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    vectorstore = AstraDBVectorStore(
        collection_name="main_v2",
        embedding=embeddings,
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_APPLICATION_TOKEN,
        namespace=ASTRA_DB_NAMESPACE,
    )

    print(f"Querying vectorstore for: {query}")

    retriever = vectorstore.as_retriever()
    retrieved_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    return { "response": await query_model(context, query) }


@app.post("/login/")
async def handle_login_request(request: Request):
    """Handle POST request, process Google token, create sessions, and cookies for frontend communication"""
    data = await request.json()
    token = data.get("token")

    session_id = auth.create_session(token)

    if (session_id):
        return cookie.create_cookie(session_id)
    else:
        return {"response": "Error in logging process. Try again."}

@app.post("/logout/")
async def handle_logout_request():
    """Handle POST request, retrieve session for email id, destory session and cookies"""

    destruction_session = auth.destroy_session()

    if (destruction_session):
        return cookie.destroy_cookie()
    else:
        return { "response": "Error in logging out process. Try again." }