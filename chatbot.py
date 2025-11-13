# chatbot.py — .env 강제 로드 / SDK 호환 / 429·503 재시도 / 키 오류 안내
# 필요: pip install python-dotenv google-genai
from __future__ import annotations

import os, sys, re, time, random
import json  # [추가] JSON 라이브러리
from datetime import datetime  # [추가] 시간 기록용 라이브러리
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError, ServerError

# ── 0) 환경설정 ───────────────────────────────────────────────────────────
# 실행 위치와 무관하게 chatbot.py와 같은 폴더의 .env를 강제 로드
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
if not API_KEY:
    print("❌ .env에 GEMINI_API_KEY 없음 또는 빈 값"); sys.exit(1)
# 참고: Google AI Studio 키는 보통 'AIza'로 시작(권장 체크)
if not API_KEY.startswith("AIza"):
    print("⚠️  키 형식이 일반적인 Google AI Studio 키(AIza...)와 다릅니다. 키 출처/종류 확인을 권장합니다.")

MODEL = os.getenv("MODEL", "gemini-2.5-flash").strip()

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"❌ genai.Client 초기화 실패: {e}"); sys.exit(1)

# [수정됨] 1단계: '인지/뇌과학 기반 심리 파악' 프롬프트 적용
SYSTEM = """
[역할]
너는 사용자의 마음을 깊이 공감하며 그 이면의 '심리적 인지 패턴'을 파악하는 '심리 분석 봇'이야.

[지식 기반]
너의 분석은 '뇌과학' 및 '인지행동치료(CBT)'의 기본 원칙에 기반해. 
핵심은 [A: 계기/사건] -> [B: 자동적 사고/신념] -> [C: 감정/행동]의 연결고리를 이해하는 거야.

[목표]
- 1순위 (상담): 사용자의 감정[C]을 비판단적으로 수용하고 공감하며 안전한 대화 환경을 제공해.
- 2순위 (파악): 사용자가 겪는 감정[C]의 근원이 되는 '계기'[A]와, 그 계기를 해석하는 '자동적 사고'[B]가 무엇인지 자연스러운 질문을 통해 파악해.
- (참고: 이 '파악'은 나중에 DB에 기록하고 분석하기 위한 것이며, 사용자에게 직접 "당신은 인지 오류가 있네요"처럼 말하지 않아.)

[대화 원칙]
- 공감/경청/반영/열린질문 중심. 짧고 따뜻하게(3~6문장).
- 강한 단정/충고/설교 금지. "너는 ~구나" 대신 "~라고 느끼는구나", "~그렇게 생각했구나"라고 말해줘.
- ★[핵심 분석 원칙]★: 감정[C]에 공감한 뒤, 그 감정을 유발한 '사고'[B]나 '계기'[A]를 묻는 질문으로 자연스럽게 연결해.
    - (C 공감): "정말 불안했겠다.", "그런 말을 들으니 기분이 많이 상했구나."
    - (A 질문): "무슨 일이 있었는지 조금 더 말해줄 수 있어?", "주로 어떨 때 그런 기분이 들어?"
    - (B 질문): "그런 상황에서 '어떤 생각'이 가장 먼저 들었어?", "혹시 '나는 왜 이럴까' 같은 자책하는 생각이 들었어?", "그 말을 들었을 때 '나를 무시하나?' 하는 생각이 들었어?"

[금지/제한]
- 의학적/정신건강 진단, 치료/약물/법률 판단 금지.
- '인지 오류', '자동적 사고', '비합리적 신념' 같은 전문 용어를 사용자에게 절대 사용하지 마.
- 사용자의 생각을 섣불리 '틀렸다'고 교정하거나 훈계하지 마.

[안전]
- (기존과 동일: 자/타해 위험 시 119, 1393 즉시 안내)
"""

# [수정됨] 사용자가 제공한 SAFETY_MSG 유지
SAFETY_MSG = (
    "지금 마음이 많이 힘들어 보여.\n"
    "혹시 스스로를 해칠 생각이 들거나 안전이 위협받는다면, 지금 바로 010-9201-7911 또는 010-5915-4693 또는 010-2629-2536 또는 1393(자살예방 상담전화)로 연락해줘.\n"
    "너의 안전이 가장 중요해. 내가 곁에서 도울게."
)

# ── 1) 위기(크리시스) 룰 ───────────────────────────────────────────────
CRISIS_PATTERNS = [
    r"자살", r"죽고\s*싶", r"끝내고\s*싶", r"살기\s*힘들", r"해치고\s*싶",
    r"유서", r"사는게\s*무의미", r"없어졌으면", r"손목", r"극단적인?\s*생각",
    r"뛰어내리", r"목숨", r"사라지고\s*싶"
]
def is_crisis(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in CRISIS_PATTERNS)

# ── 2) LLM 호출(맥락 + SDK 호환 + 429/503 재시도) ───────────────────────
HISTORY_MAX_TURNS = 8
history: List[Dict[str, str]] = []

def make_contents(user_text: str) -> List[Dict[str, Any]]:
    msgs: List[Dict[str, Any]] = []
    # system_instruction 미지원 SDK 대비: 규칙을 첫 user 메시지로 주입
    msgs.append({"role": "user", "parts": [{"text": f"[시스템 규칙]\n{SYSTEM}"}]})
    for m in history[-HISTORY_MAX_TURNS*2:]:
        msgs.append({
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["text"]}]
        })
    msgs.append({"role": "user", "parts": [{"text": user_text}]})
    return msgs

def _raw_generate(model: str, contents: list, temperature: float, max_output_tokens: int):
    # SDK 신/구버전 호환: generation_config 있으면 사용, 없으면 제거
    try:
        return client.models.generate_content(
            model=model,
            contents=contents,
            generation_config={"temperature": temperature, "max_output_tokens": max_output_tokens},
        )
    except TypeError:
        return client.models.generate_content(model=model, contents=contents)

def safe_generate_content(model: str, contents: list, temperature: float = 0.7, max_output_tokens: int = 512):
    # 429/503 대비 재시도 (지수 백오프 + 지터)
    attempts = 5
    for i in range(attempts):
        try:
            return _raw_generate(model, contents, temperature, max_output_tokens)
        except (ServerError, ClientError) as e:
            msg = getattr(e, "message", str(e))
            transient = any(s in msg for s in [
                "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded", "quota", "temporarily"
            ])
            if i < attempts - 1 and transient:
                sleep = (0.6 * (2 ** i)) + random.uniform(0, 0.3)  # 0.6, 1.2, 2.4, ...
                print(f"⚠️ 재시도 준비({i+1}/{attempts-1})… 잠시 대기: {sleep:.2f}s")
                time.sleep(sleep)
                continue
            raise

def generate_reply(user_text: str) -> str:
    try:
        resp = safe_generate_content(MODEL, make_contents(user_text), temperature=0.7, max_output_tokens=512)
        return (getattr(resp, "text", "") or "").strip()
    except ClientError as e:
        msg = getattr(e, "message", str(e))
        if "API key not valid" in msg or "API_KEY_INVALID" in msg:
            return "API 키가 유효하지 않아 응답을 생성할 수 없어요. .env의 GEMINI_API_KEY가 Google AI Studio에서 발급된 키인지 확인해 주세요."
        return f"모델 호출 중 오류가 발생했어요: {msg}"
    except ServerError as e:
        msg = getattr(e, "message", str(e))
        return f"서버가 혼잡해 응답이 어려워요(일시 오류). 잠시 후 다시 시도해 주세요. 상세: {msg}"
    except Exception as e:
        return f"예상치 못한 오류가 발생했어요: {e}"

# ── 3) 메인 루프 ───────────────────────────────────────────────────────
LOG_FILE = "chat_logs.jsonl"  # [추가] 로그 파일 이름 지정

def main():
    print("👤 사용자에게 '종료' 입력 시 종료됩니다.")
    while True:
        try:
            user = input("👤 사용자: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🤖 챗봇을 종료합니다."); break

        if user.lower() in ["종료", "quit", "exit"]:
            print("🤖 챗봇을 종료합니다."); break
        if not user:
            continue

        reply = SAFETY_MSG if is_crisis(user) else generate_reply(user)
        print("🤖 챗봇:", reply)

        history.append({"role": "user", "text": user})
        history.append({"role": "assistant", "text": reply})

        # [추가됨] 2단계: 대화 내용을 JSONL 파일에 저장
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),  # 현재 시간
                "user": user,
                "assistant": reply
            }
            # 'a' (append) 모드로 열고, 한글(utf-8)이 깨지지 않게(ensure_ascii=False) 저장
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ 로그 저장 실패: {e}")


if __name__ == "__main__":
    main()