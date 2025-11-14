# src/mongo.py
import os
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient

load_dotenv(find_dotenv(usecwd=True))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB  = os.getenv("MONGO_DB", "psy")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
_db = _client[MONGO_DB]

def count_events() -> int:
    return _db["events"].count_documents({})

def top_labels(limit: int = 10):
    pipeline = [
        {"$group": {"_id": "$payload.label", "c": {"$sum": 1}}},
        {"$sort": {"c": -1}},
        {"$limit": int(limit)},
    ]
    return list(_db["events"].aggregate(pipeline))

__all__ = ["count_events", "top_labels"]
