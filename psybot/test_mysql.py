import pymysql

print("🔍 MySQL 접속 테스트 시작")

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="pass",  # docker exec로 확인한 그 비밀번호
)

print("✅ 연결 성공!")
conn.close()
print("🔚 연결 종료")
