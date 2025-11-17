from pathlib import Path
from contextlib import contextmanager
import os

import pymysql
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ── .env 불러오기 ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "pass")
MYSQL_DB = os.getenv("MYSQL_DB", "psy")

# ── FastAPI에서 사용하는 기본 커넥션 헬퍼 ─────────────────────
@contextmanager
def get_conn():
    """
    MySQL(pymysql) 커넥션을 열고, with 블록이 끝나면 자동 commit/rollback + close
    사용법: with get_conn() as conn: ...
    """
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False,
        charset="utf8mb4",
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ── /stats/labels 에서 쓸 수 있는 SQLAlchemy 엔진 (선택) ──────
MYSQL_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
)
engine = create_engine(MYSQL_URL, future=True, echo=False)