"""Helper module to initialize and return a MongoDB client."""

from os import getenv  # Standard imports first
from pymongo import MongoClient  # Third-party imports next

MONGO_DB_URI = getenv("MONGO_DB_URI")

def get_mongo_client():
    """Return a MongoDB client using the configured URI."""
    client = MongoClient(MONGO_DB_URI)
    return client
