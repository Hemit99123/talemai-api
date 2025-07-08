from pymongo import MongoClient
from os import getenv 
from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId

MONGO_DB_URL = getenv("MONGO_DB_URL")

client = MongoClient(MONGO_DB_URL)

def get_chat_history(user_id: str) -> List[Dict[str, Any]]:
    db = client['chat_database']
    collection = db['chat_history']
    chat_history = list(collection.find({"user_id": user_id}))
    return chat_history

def save_chat_message(user_id: str, query: str, response: str) -> Dict[str, Any]:
    db = client['chat_database']
    collection = db['chat_history']
    chat_message = {
        "user_id": user_id,
        "message": query,
        "response": response,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(chat_message)
    return chat_message

def delete_chat_history(user_id: str) -> int:
    db = client['chat_database']
    collection = db['chat_history']
    result = collection.delete_many({"user_id": user_id})
    return result.deleted_count

def delete_one_chat(chat_id: ObjectId) -> int:
    db = client['chat_database']
    collection = db['chat_history']
    result = collection.delete_one({"_id": chat_id})
    return result.deleted_count 