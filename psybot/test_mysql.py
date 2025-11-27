import pymysql

print("🔍 MySQL 접속 테스트 시작")

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="pass",  # 실제 비번에 맞게
)

print("✅ 연결 성공!")
conn.close()
print("🔚 연결 종료")
