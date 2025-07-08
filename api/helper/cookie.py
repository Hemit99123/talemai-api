from fastapi.responses import JSONResponse
from os import getenv

ENV = getenv("ENV", "development")

content = { "response": "Success." }

def create_cookie(sess_id: str):

    response = JSONResponse(content=content)
    is_prod = getenv("ENV", "development") == "production"

    response.set_cookie(
        key="session-id",
        value=sess_id,
        httponly=True,
        # Set SameSite to None for cross-site cookies in production
        # Lax is used for same-site cookies in development (localhost is the same site)
        samesite="None" if is_prod else "Lax",
        # Secure flag should be set to True in production for HTTPS
        secure=is_prod,
    )
    return response

def destroy_cookie():
    response = JSONResponse(content=content)
    response.delete_cookie(key="session-id")
    return response