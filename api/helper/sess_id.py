import uuid
import secrets

def generate_random_id():
    uid = uuid.uuid4().hex  
    extra = secrets.token_hex(8)  # 16 additional random hex characters for extra randomization
    return f"{uid}-{extra}"