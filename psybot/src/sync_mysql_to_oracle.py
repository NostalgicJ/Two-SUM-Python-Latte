import os, math
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import oracledb

load_dotenv()

# MySQL 쪽 (SQLAlchemy)
mysql_url = os.getenv("MYSQL_URL")
src = create_engine(mysql_url, future=True, pool_pre_ping=True)

# Oracle 쪽 (Thin)
dsn  = os.getenv("ORACLE_DSN", "127.0.0.1/XEPDB1")
user = os.getenv("ORACLE_USER", "app")
pwd  = os.getenv("ORACLE_PASS", "pass")

# 페이징으로 가져오기 (메모리 과사용 방지)
PAGE = 2000

def fetch_total():
    with src.connect() as c:
        (total,) = c.execute(text("SELECT COUNT(*) FROM assessments")).one()
    return int(total)

def fetch_page(offset, limit):
    with src.connect() as c:
        rows = c.execute(text("""
            SELECT user_id, tool, external_id, score, label, ts, data_source, version, ingested_at
            FROM assessments
            ORDER BY id
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).all()
    return rows

merge_sql = """
MERGE INTO assessments tgt
USING (SELECT :tool AS tool, :external_id AS external_id FROM dual) src
ON (tgt.tool = src.tool AND tgt.external_id = src.external_id)
WHEN MATCHED THEN UPDATE SET
  user_id = :user_id,
  score = :score,
  label = :label,
  ts = :ts,
  data_source = :data_source,
  version = :version,
  ingested_at = :ingested_at
WHEN NOT MATCHED THEN
  INSERT (user_id, tool, external_id, score, label, ts, data_source, version, ingested_at)
  VALUES (:user_id, :tool, :external_id, :score, :label, :ts, :data_source, :version, :ingested_at)
"""

def to_params(row):
    d = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    return {
        "user_id": d["user_id"],
        "tool": d["tool"],
        "external_id": d["external_id"],
        "score": d["score"],
        "label": d["label"],
        # MySQL DATETIME → Oracle TIMESTAMP: 문자열/파서 없이 그대로 전달 가능 (Python datetime)
        "ts": d["ts"],
        "data_source": d["data_source"],
        "version": d["version"],
        "ingested_at": d["ingested_at"],
    }

def main():
    total = fetch_total()
    print(f"Total rows to sync: {total}")
    if total == 0:
        return

    with oracledb.connect(user=user, password=pwd, dsn=dsn) as con:
        with con.cursor() as cur:
            for page_idx in range(math.ceil(total / PAGE)):
                offset = page_idx * PAGE
                rows = fetch_page(offset, PAGE)
                params = [to_params(r) for r in rows]
                cur.executemany(merge_sql, params)
                con.commit()
                print(f"  → synced {offset + len(params)}/{total}")
    print("✅ Oracle sync done")

if __name__ == "__main__":
    main()
