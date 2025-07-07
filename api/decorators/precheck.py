from helper import auth
from fastapi import Request

def decorator(func):

    # request is used within the logic of decorator so it is passed through wrapper
    # this allows us to access the request object and its properties
    # such as cookies, headers, etc. within the decorator logic
    
    def wrapper(request: Request):
        session_validity = auth.get_session(request)

        if (session_validity):
            return func()
        else:
            return {"response": "Unauthorized access. Please login."}
    return wrapper

