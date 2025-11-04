# chatbot.py  (google-genai 사용)
from dotenv import load_dotenv
import os, sys
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ .env에 GEMINI_API_KEY 없음"); sys.exit(1)

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

SYSTEM = "너는 친절한 심리상담 챗봇이야."
print("👤 사용자에게 '종료' 입력 시 종료됩니다.")

while True:
    user = input("👤 사용자: ")
    if user.lower() in ["종료","quit","exit"]:
        print("🤖 챗봇을 종료합니다."); break
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=[
                {"role":"user","parts":[{"text": SYSTEM}]},
                {"role":"user","parts":[{"text": user}]},
            ],
        )
        print("🤖 챗봇:", resp.text)
    except Exception as e:
        print("❌ 오류:", e)
