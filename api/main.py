"""Main entry point for the Talem AI FastAPI server."""

from fastapi import FastAPI
from helper import ai
from pydantic import BaseModel

app = FastAPI()


class QueryModal(BaseModel):
    """Schema for incoming POST request with user query."""
    query: str


@app.get("/")
async def read_root():
    """Health check route for the server."""
    return {"message": "Talem AI server"}


@app.post("/")
async def handle_query(request: QueryModal):
    """Handle POST request, process query, and return AI-generated response."""
    ai_response = ai.fetch_and_query(request.query)
    return {"content": ai_response}
