"""Precheck decorator to ensure request has an authenticated user."""

import functools
from fastapi import Request
from helper.auth import get_session_email


def decorator(func):
    """Decorator that checks if the request has a valid session email."""
    @functools.wraps(func)
    async def wrapper(request: Request):
        email = await get_session_email(request)
        if email:
            return await func(request)
        return {"response": "Unauthorized access. Please login."}
    return wrapper
