# web_api.py — FastAPI로 chatbot.py 기능을 웹에서 쓰기

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 기존 콘솔 챗봇 로직 재사용
from chatbot import (
    generate_reply,
    select_skills,
    is_crisis,
    SAFETY_MSG,
    history,
    create_psybot_session,
    log_psybot_message,
)

app = FastAPI()

# CORS (정적 서버: 5500포트, 기타 등에서 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 필요하면 정확한 origin으로 좁혀도 됨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# psybot 세션 한 번 만들어두기 (DB 서버 안 켜져 있으면 0으로 떨어짐 → 그냥 로그만 안 찍힘)
SESSION_ID = create_psybot_session()

# 동일 문장 반복 체크용 (콘솔 버전 로직 가져온 것)
_prev_user: str | None = None
_same_count: int = 0


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    global _prev_user, _same_count, SESSION_ID

    user = req.message.strip()
    if not user:
        return ChatResponse(
            reply="지금 뭐라고 적어야 할지 모르겠다면, 그냥 현재 기분을 한 단어로만 적어줘도 괜찮아."
        )

    # DB 쪽 로그 남기기 (psybot API 켜져 있을 때만)
    if SESSION_ID:
        log_psybot_message(SESSION_ID, user)

    # 반복 입력 체크 → 스킬 상세 모드
    if _prev_user is not None and user == _prev_user:
        _same_count += 1
    else:
        _prev_user = user
        _same_count = 1
    force_detail = _same_count >= 2

    # 위기 감지
    if is_crisis(user):
        reply = SAFETY_MSG
    else:
        skills = select_skills(user)
        reply = generate_reply(user, skills, force_detail)

    # chatbot.py가 쓰는 history도 같이 업데이트
    history.append({"role": "user", "text": user})
    history.append({"role": "assistant", "text": reply})

    return ChatResponse(reply=reply)
