# src/db.py — SQLite 기본 + (옵션) MySQL, Mongo 연결 제공
import os
import sqlite3
from contextlib import contextmanager

from dotenv import load_dotenv

# (옵션) MySQL, Mongo는 설치돼 있지 않아도 동작하도록 지연 임포트 시도
try:
    from sqlalchemy import create_engine  # type: ignore
except Exception:  # SQLAlchemy 미설치 시 None 처리
    create_engine = None  # type: ignore

try:
    from pymongo import MongoClient  # type: ignore
except Exception:  # PyMongo 미설치 시 None 처리
    MongoClient = None  # type: ignore

load_dotenv()

# ---------- SQLite (기본) ----------
DB_PATH = os.getenv("DB_PATH", "./psybot.db")

@contextmanager
def get_conn():
    """
    SQLite 연결 컨텍스트 매니저.
    - 외래키 강제: ON
    - 자동 커밋: with 블록 정상 종료 시 commit
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# ---------- MySQL (선택) ----------
# .env 예시: MYSQL_URL=mysql+pymysql://root:pass@127.0.0.1:3306/psy
MYSQL_URL = os.getenv("MYSQL_URL", "").strip()
if MYSQL_URL and create_engine:
    # pool_pre_ping=True 로 끊어진 커넥션 자동 복구
    engine = create_engine(MYSQL_URL, future=True, pool_pre_ping=True)
else:
    engine = None  # SQLAlchemy 없거나 URL 미지정 시

# ---------- MongoDB (선택) ----------
# .env 예시:
# MONGO_URL=mongodb://127.0.0.1:27017
# MONGO_DB=psy
MONGO_URL = os.getenv("MONGO_URL", "").strip()
MONGO_DB  = os.getenv("MONGO_DB", "psy").strip()
if MONGO_URL and MongoClient:
    mongo_client = MongoClient(MONGO_URL)         # tz_aware=False 기본
    mdb = mongo_client[MONGO_DB]
else:
    mongo_client = None
    mdb = None

__all__ = [
    "get_conn",  # SQLite 컨텍스트
    "engine",    # MySQL SQLAlchemy Engine (없으면 None)
    "mongo_client", "mdb",  # Mongo Client/DB (없으면 None)
]
