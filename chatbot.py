# chatbot.py — 버전 호환 픽스( generation_config / system_instruction 미지원 대응 )
# 필요: pip install python-dotenv google-genai requests
from dotenv import load_dotenv
import os, sys, json, re, requests
from uuid import uuid4
from typing import List, Dict, Any
from google import genai

# ── 0) 환경설정 ───────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ .env에 GEMINI_API_KEY 없음"); sys.exit(1)

ANALYZE_URL = os.getenv("ANALYZE_URL", "http://localhost:8000/analyze")
LOG_URL     = os.getenv("LOG_URL", "http://localhost:8000/log")
USE_ANALYZE = os.getenv("USE_ANALYZE", "true").lower() in ("1","true","yes","y")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY)

SYSTEM = """
[역할]
너는 마음을 가볍게 해주는 심리 상담 보조 챗봇이야.

[목표]
- 사용자의 감정을 비판단적으로 반영하고, 부담 없는 다음 한 걸음을 제안해.
- 문제 해결보다 사용자의 감정 인식과 안전 확보를 우선해.

[대화 원칙]
- 공감/경청/반영/열린질문 중심. 짧고 따뜻하게(3~6문장).
- 모호하면 확인 질문을 1개만. 강한 단정/충고/설교 금지.
- 사용자의 표현을 1~2곳 핵심어로 부드럽게 되비쳐줘(“~라고 느껴지는구나” 수준).

[금지/제한]
- 의학적/정신건강 진단, 치료/약물/법률 판단을 하지 마.
- 증거 없이 사실 단정하지 마. 위험 행동을 구체적으로 제안하거나 미화하지 마.
- 개인정보 요청 최소화.

[안전]
- 자/타해 위험이 의심되면 장황한 조언 없이 즉시 안전 안내로 전환해(119, 1393).
- 안전 안내는 간결하고 따뜻하게, 구체 연락처 포함.

[출력 스타일]
- 한국어, 반말 대신 부드럽고 존중하는 말투.
- 필요 시 짧은 목록(● 2~3개) 허용. 과도한 이모지는 지양.
"""


SAFETY_MSG = (
    "지금 마음이 많이 힘들어 보여.\n"
    "혹시 스스로를 해칠 생각이 들거나 안전이 위협받는다면, 지금 바로 119 또는 1393(자살예방 상담전화)로 연락해줘.\n"
    "너의 안전이 가장 중요해. 내가 곁에서 도울게."
)

# ── 1) 위기(크리시스) 룰 ───────────────────────────────────────────────
CRISIS_PATTERNS = [
    r"자살", r"죽고\s*싶", r"끝내고\s*싶", r"살기\s*힘들", r"해치고\s*싶",
    r"유서", r"사는게\s*무의미", r"없어졌으면", r"손목", r"극단적인\s*생각"
]
def is_crisis(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in CRISIS_PATTERNS)

# ── 2) 분석/로그 API 래퍼 ──────────────────────────────────────────────
def analyze_http(session_id: str, text: str) -> Dict[str, Any]:
    if not USE_ANALYZE:
        return {"sentiment":"neutral","stress":1,"risk":0,"topics":[],"suggested_next_questions":[]}
    try:
        r = requests.post(
            ANALYZE_URL,
            json={"session_id": session_id, "text": text, "lang":"ko"},
            timeout=3
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"sentiment":"neutral","stress":1,"risk":0,"topics":[],"suggested_next_questions":[]}

def log_http(session_id: str, role: str, text: str, analysis: Dict[str,Any] | None, consent: bool):
    if not consent: return
    try:
        requests.post(
            LOG_URL,
            json={"session_id": session_id, "role": role, "text": text, "analysis": analysis},
            timeout=2
        )
    except Exception:
        pass

# ── 3) LLM 호출(맥락 + 버전 호환 래퍼) ────────────────────────────────
HISTORY_MAX_TURNS = 8
history: List[Dict[str,str]] = []

def make_contents(user_text: str) -> List[Dict[str,Any]]:
    msgs: List[Dict[str,Any]] = []
    # (중요) 구버전 호환: system_instruction 대신 첫 메시지로 규칙 주입
    msgs.append({"role":"user","parts":[{"text": f"[시스템 규칙]\n{SYSTEM}"}]})
    for m in history[-HISTORY_MAX_TURNS*2:]:
        msgs.append({
            "role": "user" if m["role"]=="user" else "model",
            "parts":[{"text": m["text"]}]
        })
    msgs.append({"role":"user","parts":[{"text": user_text}]})
    return msgs

def safe_generate_content(model: str, contents: list, temperature: float = 0.7, max_output_tokens: int = 512):
    """
    SDK 버전 차이를 흡수하기 위한 래퍼:
    - 신버전: generation_config 지원
    - 구버전: 해당 키워드 제거하고 재시도
    """
    try:
        return client.models.generate_content(
            model=model,
            contents=contents,
            generation_config={"temperature": temperature, "max_output_tokens": max_output_tokens},
        )
    except TypeError:
        # 구버전: generation_config 미지원 → 옵션 제거하고 호출
        return client.models.generate_content(
            model=model,
            contents=contents
        )

def generate_reply(user_text: str) -> str:
    resp = safe_generate_content(
        model=MODEL,
        contents=make_contents(user_text),
        temperature=0.7,
        max_output_tokens=512
    )
    return (getattr(resp, "text", "") or "").strip()

# ── 4) 메인 루프 ───────────────────────────────────────────────────────
def main():
    print("👤 사용자에게 '종료' 입력 시 종료됩니다.")
    consent = input("👤 분석/익명 저장에 동의하니? (y/n): ").strip().lower() == "y"
    session_id = str(uuid4())

    while True:
        user = input("👤 사용자: ").strip()
        if user.lower() in ["종료","quit","exit"]:
            print("🤖 챗봇을 종료합니다."); break

        # (1) 위기 1차 룰
        crisis_flag = is_crisis(user)

        # (2) 외부 분석(B팀)
        analysis = analyze_http(session_id, user)
        risk = int(analysis.get("risk", 0))

        # (3) 응답 결정
        if crisis_flag or risk >= 2:
            reply = SAFETY_MSG
        else:
            reply = generate_reply(user)
            q = (analysis.get("suggested_next_questions") or [])
            if q:
                reply += "\n\n" + "혹시 괜찮다면, " + q[0]

        print("🤖 챗봇:", reply)

        # (4) 히스토리
        history.append({"role":"user","text":user})
        history.append({"role":"assistant","text":reply})

        # (5) (동의 시) 로그 저장은 전부 B팀에 위임
        log_http(session_id, "user", user, None, consent)
        log_http(session_id, "assistant", reply, analysis, consent)

if __name__ == "__main__":
    main()
