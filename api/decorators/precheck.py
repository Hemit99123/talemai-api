from helper import auth
from fastapi import Request
import functools
import inspect

def decorator(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(request: Request):
            session_validity = await auth.get_session(request) if inspect.iscoroutinefunction(auth.get_session) else auth.get_session(request)
            if session_validity:
                return await func(request)
            else:
                return {"response": "Unauthorized access. Please login."}
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(request: Request):
            session_validity = auth.get_session(request)
            if session_validity:
                return func(request)
            else:
                return {"response": "Unauthorized access. Please login."}
        return sync_wrapper
