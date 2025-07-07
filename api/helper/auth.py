import os
import requests
import redis
from dotenv import load_dotenv
from helper import sess_id
from fastapi import Request, Depends

# Load environment variables
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def create_session(token: str):
    try:
        # Send the token to Google to validate it
        response = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token}
        )

        token_status = response.status_code == 200
    
        if (token_status):

            generated_sess_id = sess_id.generate_random_id()

            # This is the contents of the session
            redis_client.hset(generated_sess_id, mapping={
                'name': response.user.name,
                'email': response.user.email,
            })

            return sess_id
        else:
            return False
    except Exception as error:
        print(error)
        return False

def destroy_session(email):
    try:
        redis_client.delete(email)
        return True
    except Exception as error:
        print(error)
        return False

def get_session(request: Request):
    sess_id = request.cookies.get("session-id")

    email = redis_client.hget(sess_id, "email")
    picture = redis_client.hget(sess_id, "picture")

    if not email or not picture:
        return None
    else:
        return { "email": email, "picture": picture }