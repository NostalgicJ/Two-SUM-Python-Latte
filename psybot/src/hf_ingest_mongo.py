import os
from datetime import datetime, timezone
from datasets import load_dataset
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME   = os.getenv("MONGO_DB", "psy")
DATASET   = os.getenv("HF_DATASET", "emotion")

client = MongoClient(MONGO_URL)  # tz_aware=False 기본 → naive datetime 사용
db = client[DB_NAME]
col = db["events"]

# 캐시에서 불러와도 됨
ds = load_dataset(DATASET, split="train")

label_map = {0:"sadness",1:"joy",2:"love",3:"anger",4:"fear",5:"surprise"}

# UTC-aware → naive UTC (tz 제거) : PyMongo 기본과 맞춤
now = datetime.now(timezone.utc).replace(tzinfo=None)

# 인덱스(최초 1회)
col.create_index([("user_id",1),("ts",1)])
col.create_index([("data_source",1),("type",1)])
col.create_index([("tool",1),("external_id",1)], unique=True)

ops = []
for i, r in enumerate(ds):
    doc = {
        "user_id": 0,
        "type": "emotion",
        "tool": f"hf_{DATASET}",
        "external_id": str(i),
        "payload": {
            "label": label_map.get(int(r["label"]), str(r.get("label"))),
            "score": 1.0
        },
        "ts": now,            # naive UTC
        "data_source": "huggingface",
        "version": "v1",
        "ingested_at": now    # naive UTC
    }
    # ❗ dict 아님. UpdateOne 객체로 넣기
    ops.append(UpdateOne(
        {"tool": doc["tool"], "external_id": doc["external_id"]},
        {"$set": doc},
        upsert=True
    ))

if ops:
    print("USING UpdateOne, ops len =", len(ops))
    res = col.bulk_write(ops, ordered=False)
    print(f"✅ Mongo upsert ok: upserted={res.upserted_count}, modified={res.modified_count}")
else:
    print("no ops")
