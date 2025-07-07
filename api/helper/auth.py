import os
import requests
import redis
from dotenv import load_dotenv
from helper import sess_id
from fastapi import Request

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

        result = response.json()

        name = result["given_name"] + " " + result["family_name"]
        email = result["email"]

        token_status = response.status_code == 200

        if (token_status):

            generated_sess_id = sess_id.generate_random_id()

            # This is the contents of the session
            redis_client.hset(generated_sess_id, mapping={
                "name": name,
                "email": email
            })

            return generated_sess_id
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

async def get_session(request: Request):
    # get cookie with session id
    sess_id = request.cookies.get("session-id")

    if not sess_id:
        return False

    # find session attributes using session id (hashmap allows individual key-value pairs access)
    name = redis_client.hget(sess_id, "name")
    email = redis_client.hget(sess_id, "email")

    if not name or not email:
        return False
    else:
        return { 
            "name": name,
            "email": email, 
        }