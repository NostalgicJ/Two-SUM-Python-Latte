import os, time
from dotenv import load_dotenv
import oracledb

load_dotenv()
dsn  = os.getenv("ORACLE_DSN", "127.0.0.1/XEPDB1")
user = os.getenv("ORACLE_USER", "app")
pwd  = os.getenv("ORACLE_PASS", "pass")

sql = open("sql/schema.oracle.sql","r",encoding="utf-8").read()

# 준비될 때까지 최대 2분 재시도
for i in range(60):
    try:
        with oracledb.connect(user=user, password=pwd, dsn=dsn) as con:
            with con.cursor() as cur:
                for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
                    cur.execute(stmt)
            con.commit()
        print("✅ Oracle schema applied")
        break
    except Exception as e:
        if i == 59:
            raise
        time.sleep(2)
