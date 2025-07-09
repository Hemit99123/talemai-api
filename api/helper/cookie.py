"""Cookie helper module to create and destroy session cookies for authentication."""

from os import getenv  # Standard import first
from fastapi.responses import JSONResponse  # Third-party import

ENV = getenv("ENV", "development")
content = {"response": "Success."}

def create_cookie(sess_id: str):
    """Create a session cookie with appropriate settings based on environment."""
    response = JSONResponse(content=content)
    is_prod = ENV == "production"

    response.set_cookie(
        key="session-id",
        value=sess_id,
        httponly=True,
        samesite="None" if is_prod else "Lax",
        secure=is_prod,
    )
    return response

def destroy_cookie():
    """Destroy the session cookie by removing it from the response."""
    response = JSONResponse(content=content)
    response.delete_cookie(key="session-id")
    return response
