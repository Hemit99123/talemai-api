"""Main entry point for the Talem AI FastAPI server."""

from fastapi import FastAPI, Response
from helper import ai
from pydantic import BaseModel
from helper import auth
from helper import cookie 

app = FastAPI()


class QueryModal(BaseModel):
    """Schema for incoming POST request with user query."""
    query: str

# Needed to allow cookies to be sent to frontend
@app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai.talem.org"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["Access-Control-Allow-Headers", 'Content-Type', 'Authorization', 'Access-Control-Allow-Origin'],
)

@app.get("/")
async def handle_index_request():
    """Health check route for the server."""

    return {"response": "Talem AI server"}


@app.post("/")
async def handle_chat_request(request: QueryModal):
    """Handle POST request, process query, and return AI-generated response."""

    ai_response = ai.fetch_and_query(request.query)
    return {"response": ai_response}


@app.post("/login/")
async def handle_login_request(request: QueryModal, response: Response):
    """Handle POST request, process Google token, create sessions, and cookies for frontend communication"""

    session_id = auth.create_session(request.token)

    if (session_id):
        return cookie.create_cookie(session_id)
    else:
        return {"response": "Error in logging process. Try again."}

@app.post("/logout/"):
async def handle_logout_request(request:QueryModal, response: Response):
    """Handle POST request, retrieve session for email id, destory session and cookies"""

    destruction_session = auth.destroy_session()

    if (destruction_session):
        return cookie.destroy_cookie()
    else:
        return { "response": "Error in logging out process. Try again." }