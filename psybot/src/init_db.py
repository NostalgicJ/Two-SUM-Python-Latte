from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "sql" / "schema.sql"
SEED = ROOT / "sql" / "seed.sql"
DB = ROOT / "psybot.db"

def run_sql(path: Path, conn):
    with open(path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

def safe_add_column(conn, table, col, decl):
    cur = conn.execute(f"PRAGMA table_info({table})")
    names = {r[1] for r in cur.fetchall()}
    if col not in names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")

if __name__ == "__main__":
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")

    # 스키마 적용
    run_sql(SCHEMA, conn)

    # 씨드(있을 때만)
    try:
        if SEED.exists():
            run_sql(SEED, conn)
    except sqlite3.Error as e:
        print("[seed skipped]", e)

    # 기존 DB에도 컬럼 안전 추가
    safe_add_column(conn, "inference_result", "valence", "REAL")
    safe_add_column(conn, "inference_result", "arousal", "REAL")

    conn.commit()
    conn.close()
    print("DB initialized at", DB)
