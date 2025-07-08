from helper.auth import get_session_email
from fastapi import Request
import functools

def decorator(func):
    @functools.wraps(func)
    async def wrapper(request: Request):
        email = await get_session_email(request)
        if email:
            return await func(request)
        return {"response": "Unauthorized access. Please login."}
    return wrapper
    