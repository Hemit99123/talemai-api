from helper import auth
from fastapi import Request
import functools

def decorator(func):
    @functools.wraps(func)
    async def wrapper(request: Request):
        session_valid = await auth.get_session(request)
        if session_valid:
            return await func(request)
        return {"response": "Unauthorized access. Please login."}
    return wrapper
    