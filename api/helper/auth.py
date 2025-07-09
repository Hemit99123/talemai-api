"""Authentication helper module for managing session creation, destruction, and retrieval."""

import os
import requests
import redis
from dotenv import load_dotenv
from fastapi import Request
from helper.session_id import generate_random_id

# Load environment variables
load_dotenv()

REDIS_URI = os.getenv("REDIS_URI")
redis_client = redis.from_url(REDIS_URI, decode_responses=True)

def create_session(token: str):
    """Validate a Google token and create a session in Redis."""
    try:
        response = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
            timeout=5
        )

        result = response.json()

        name = result["given_name"] + " " + result["family_name"]
        email = result["email"]

        token_status = response.status_code == 200
        if token_status:
            session_id = generate_random_id()

            redis_client.hset(session_id, mapping={
                "name": name,
                "email": email
            })

            expiry_time = 60 * 60 * 24 * 7  # 7 days
            redis_client.expire(session_id, expiry_time)

            return session_id
        return False
    except requests.RequestException as error:
        print(error)
        return False

def destroy_session(request: Request):
    """Destroy a session in Redis based on the session-id cookie."""
    sess_id = request.cookies.get("session-id")
    try:
        redis_client.delete(sess_id)
        return True
    except redis.RedisError as error:
        print(error)
        return False

async def get_session_email(request: Request):
    """Retrieve the email from Redis using the session-id cookie."""
    sess_id = request.cookies.get("session-id")

    if not sess_id:
        return False

    email = redis_client.hget(sess_id, "email")

    if not email:
        return False

    return email
