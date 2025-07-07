from helper import auth
from fastapi import Request

def decorator(func):
    def wrapper(request: Request):
        session_validity = auth.get_session(request)

        if (session_validity):
            return func()
        else:
            return {"response": "Unauthorized access. Please login."}
    return wrapper

