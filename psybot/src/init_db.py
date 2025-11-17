from pathlib import Path

import pymysql

# ── 0) 경로 설정 ─────────────────────────────────────────────────────────

# 현재 파일: psybot/src/init_db.py
# ROOT:      psybot/
ROOT = Path(__file__).resolve().parents[1]

DB_NAME = "psy"  # 사용할 DB 이름

SCHEMA = ROOT / "sql" / "schema.mysql.sql"
SEED   = ROOT / "sql" / "seed.sql"


# ── 1) MySQL 커넥션 ──────────────────────────────────────────────────────

def get_mysql_conn(without_db: bool = False):
    """
    docker-compose.yml 기준:
      - host: localhost
      - port: 3306
      - user: root
      - password: pass
      - database: psy
    """
    conn_kwargs = dict(
        host="localhost",
        port=3306,
        user="root",
        password="pass",   # ← 여기 비밀번호 고정
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    if not without_db:
        conn_kwargs["database"] = DB_NAME

    return pymysql.connect(**conn_kwargs)


# ── 2) SQL 파일 실행 ─────────────────────────────────────────────────────

def run_sql_file(path: Path, conn):
    """SQL 파일 내용을 ; 기준으로 쪼개서 순서대로 실행"""
    if not path.exists():
        print(f"⚠️  파일 없음: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        script = f.read()

    statements = script.split(";")

    with conn.cursor() as cur:
        for raw in statements:
            stmt = raw.strip()
            if not stmt:
                continue
            cur.execute(stmt)


# ── 3) 메인 ──────────────────────────────────────────────────────────────

def main():
    conn = get_mysql_conn(without_db=True)
    try:
        with conn.cursor() as cur:
            # DB 없으면 생성
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci;"
            )
            cur.execute(f"USE `{DB_NAME}`;")

        print(f"📂 스키마 적용: {SCHEMA}")
        run_sql_file(SCHEMA, conn)

        print(f"📂 시드 데이터 적용(있으면): {SEED}")
        run_sql_file(SEED, conn)

        conn.commit()
        print("✅ MySQL 스키마 + 시드 적용 완료")
    except Exception as e:
        conn.rollback()
        print("❌ 오류 발생, 롤백했습니다.")
        print(e)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
