# HF -> MySQL upsert (assessments)
import os
from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv
from datasets import load_dataset
from sqlalchemy import create_engine, text

load_dotenv(find_dotenv(usecwd=True))

MYSQL_URL = os.getenv("MYSQL_URL")  # mysql+pymysql://root:pass@127.0.0.1:3306/psy
DATASET = os.getenv("HF_DATASET", "emotion")  # 기본: 'emotion'
if not MYSQL_URL:
    raise SystemExit("MYSQL_URL not set in .env")

# 엔진 (끊김 예방 옵션)
from sqlalchemy.pool import QueuePool
engine = create_engine(
    MYSQL_URL,
    future=True,
    poolclass=QueuePool,
    pool_pre_ping=True,
    pool_recycle=180,
    connect_args={"connect_timeout": 10},
)

label_map = {0: "sadness", 1: "joy", 2: "love", 3: "anger", 4: "fear", 5: "surprise"}

# tz-aware -> naive(UTC) 로 바꿔 MySQL DATETIME에 넣기
def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

UPSERT_SQL = text("""
INSERT INTO assessments
  (user_id, tool, external_id, score, label, ts, data_source, version, ingested_at)
VALUES
  (:user_id, :tool, :external_id, :score, :label, :ts, :data_source, :version, :ingested_at)
ON DUPLICATE KEY UPDATE
  user_id=VALUES(user_id),
  score=VALUES(score),
  label=VALUES(label),
  ts=VALUES(ts),
  data_source=VALUES(data_source),
  version=VALUES(version),
  ingested_at=VALUES(ingested_at)
""")

def main():
    print(f"loading HF dataset: {DATASET} (train split)")
    ds = load_dataset(DATASET, split="train")

    now = utc_now_naive()
    tool = f"hf_{DATASET}"
    rows = []

    for i, r in enumerate(ds):
        # HF emotion: {'text': ..., 'label': 0..5}
        label = label_map.get(int(r.get("label", -1)), None)
        if label is None:
            continue
        rows.append({
            "user_id": 0,
            "tool": tool,
            "external_id": str(i),
            "score": None,
            "label": label,
            "ts": now,                  # 모두 동일 timestamp로 적재(원하면 r별 시간 만들 수 있음)
            "data_source": "huggingface",
            "version": "v1",
            "ingested_at": now,
        })
        # 너무 커질 때 끊어서 배치 실행
        if len(rows) >= 2000:
            flush(rows)
    flush(rows)
    print("✅ HF -> MySQL ingest done")

def flush(rows):
    if not rows:
        return
    with engine.begin() as conn:         # begin() => 자동 commit/rollback
        conn.execute(UPSERT_SQL, rows)
    print(f"  inserted/upserted: {len(rows)}")
    rows.clear()

if __name__ == "__main__":
    main()
