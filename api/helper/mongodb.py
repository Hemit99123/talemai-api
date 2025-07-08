from pymongo import MongoClient
from os import getenv 

MONGO_DB_URI = getenv("MONGO_DB_URI")

def get_mongo_client():
    client = MongoClient(MONGO_DB_URI)
    return client