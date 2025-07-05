import os
import requests
import redis
from dotenv import load_dotenv
from helper import sess_id
from helper import cookie

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

        email = response.user.email
        token_status = response.status_code == 200
    
        if (token_status):

            sess_id = sess_id.generate_random_id()

            redis_client.hset(sess_id, mapping={
                'name': response.user.name,
                'picture': response.user.picture
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
    cookie_sess_id = cookie.get_cookie(request)

    email = redis_client.hget(cookie_sess_id, "email")
    picture = redis_client.hget(cookie_sess_id, "picture")

    return { "email": email, "picture": picture }