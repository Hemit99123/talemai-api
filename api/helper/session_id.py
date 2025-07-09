"""Helper module for generating secure, random session IDs."""

import uuid
import secrets

def generate_random_id():
    """Generate a secure, random session ID using UUID and extra entropy."""
    uid = uuid.uuid4().hex
    extra = secrets.token_hex(8)  # Add 16 extra hex characters for more randomness
    return f"{uid}-{extra}"
