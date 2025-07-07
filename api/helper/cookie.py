from fastapi import Request
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
        samesite="None" if is_prod else "Lax",
        secure=is_prod,
    )
    return response

def destroy_cookie():
    response = JSONResponse(content=content)
    response.delete_cookie(key="session-id")
    return response