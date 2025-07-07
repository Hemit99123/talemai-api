from helper import auth
from fastapi import Request

def precheck(func, request: Request):
    def wrapper():
        session_validity = auth.verify_session(request)

        if (session_validity):
            return func()
        else:
            return {"response": "Unauthorized access. Please login."}
    return wrapper