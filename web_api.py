# web_api.py  —  EmotAI 웹 프론트 + HTTP API

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# chatbot.py 안의 로직 재사용
from chatbot import (
    is_crisis,
    SAFETY_MSG,
    select_skills,
    generate_reply,
    history,
    create_psybot_session,
    log_psybot_message,
    USER_ID,
)

app = FastAPI(title="EmotAI Web API")

# --- CORS 설정: 어디서든 접근 가능(개발용) ---
# ngrok로 접속하는 브라우저들이 전부 허용되도록 *
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # "*" 쓸 땐 False
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 정적 파일 & 메인 페이지 서빙 설정 ---

# /static/... 으로 static 폴더의 파일들 제공
# (index.html, chat.html, about.html, app.js, styles.css 등)
app.mount("/static", StaticFiles(directory="static"), name="static")


# 루트(/)로 들어오면 랜딩 페이지 index.html 반환
@app.get("/")
def serve_index():
    # web_api.py와 같은 폴더 기준으로 static/index.html
    return FileResponse("static/index.html")


# --- psybot 세션 관리 ---
SESSION_ID: int = 0


def ensure_session():
    global SESSION_ID
    if SESSION_ID <= 0:
        SESSION_ID = create_psybot_session(USER_ID)
        print(f"web_api: psybot session = {SESSION_ID}")


# --- 요청/응답 모델 ---
class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str


# --- /chat 엔드포인트 ---
@app.post("/chat", response_model=ChatOut)
def chat_endpoint(body: ChatIn):
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty message")

    # psybot 세션 확보
    ensure_session()

    # DB에 먼저 메시지 로그 시도
    log_psybot_message(SESSION_ID, text)

    # 위기 문구 체크
    if is_crisis(text):
        reply = SAFETY_MSG
    else:
        skills = select_skills(text)
        # 웹에서는 same_count 같은 건 그냥 무시하고 force_detail=False
        reply = generate_reply(text, skills, force_detail=False)

    # 히스토리 업데이트 (LLM 맥락 유지용)
    history.append({"role": "user", "text": text})
    history.append({"role": "assistant", "text": reply})

    return ChatOut(reply=reply)
