# chatbot.py — .env 강제 로드 / SDK 호환 / 429·503 재시도 / 키 오류 안내 + RAG 심리 스킬 라이브러리 + 반복 입력 시 스킬 상세 설명
# 필요: pip install python-dotenv google-genai requests
from __future__ import annotations

import os, sys, re, time, random
import json  # JSON 로그 저장용
from datetime import datetime  # 시간 기록용
from pathlib import Path
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError, ServerError

# ── psybot API 설정 ──────────────────────────────────────────────────────
PSYBOT_API = os.getenv("PSYBOT_API", "http://127.0.0.1:8000")
USER_ID = int(os.getenv("PSYBOT_USER_ID", "1"))  # 지금 DB에 있는 '재용' 유저 id

# ── 0) 환경설정 ───────────────────────────────────────────────────────────
# 실행 위치와 무관하게 chatbot.py와 같은 폴더의 .env를 강제 로드
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
if not API_KEY:
    print("❌ .env에 GEMINI_API_KEY 없음 또는 빈 값")
    sys.exit(1)

# 참고: Google AI Studio 키는 보통 'AIza'로 시작(권장 체크)
if not API_KEY.startswith("AIza"):
    print("⚠️  키 형식이 일반적인 Google AI Studio 키(AIza...)와 다릅니다. 키 출처/종류 확인을 권장합니다.")

MODEL = os.getenv("MODEL", "gemini-2.5-flash").strip()

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"❌ genai.Client 초기화 실패: {e}")
    sys.exit(1)

# ── 시스템 프롬프트: 인지/뇌과학 기반 심리 파악 ──────────────────────────
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

# 안전 메시지
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
    """단순 키워드 매칭 기반 위기 감지."""
    return any(re.search(p, text, re.IGNORECASE) for p in CRISIS_PATTERNS)

# ── 1-1) 심리 스킬 라이브러리 (skills.json RAG-lite) ───────────────────
SKILLS_FILE = Path(__file__).with_name("skills.json")

def load_skills() -> List[Dict[str, Any]]:
    """skills.json 파일을 읽어서 리스트로 반환. 없으면 빈 리스트."""
    if not SKILLS_FILE.exists():
        return []
    try:
        with open(SKILLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"⚠️ skills.json 로드 실패: {e}")
        return []

ALL_SKILLS: List[Dict[str, Any]] = load_skills()

def score_skill(user_text: str, skill: Dict[str, Any]) -> int:
    """
    아주 단순한 점수 함수:
    - skill['keywords']에 있는 단어가 user_text에 몇 개 포함되는지 세어서 점수로 사용.
    """
    t = user_text.lower()
    keywords = skill.get("keywords", [])
    score = 0
    for kw in keywords:
        if kw.lower() in t:
            score += 1
    return score

def select_skills(user_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    사용자 문장을 보고 관련도가 높은 스킬 상위 top_k개를 선택.
    (키워드 매칭 기반 RAG-lite)
    """
    if not ALL_SKILLS:
        return []

    scored = []
    for s in ALL_SKILLS:
        sc = score_skill(user_text, s)
        if sc > 0:
            scored.append((sc, s))

    if not scored:
        return []

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_k]]

def format_skills_for_prompt(skills: List[Dict[str, Any]], force_detail: bool) -> str:
    """
    LLM에게 넘길 '내부 스킬 정보' 문자열 생성.
    force_detail=True 이면, 한 개 스킬을 골라 이름과 단계들을 더 자세히 설명하도록 강하게 요청.
    """
    if not skills:
        # 매칭되는 스킬이 없을 때는 아주 가볍게 자기 돌봄 정도만 언급하도록 안내
        return (
            "[내부 심리 스킬 추천 목록]\n"
            "현재 사용자에게 바로 제안할 만한 구체적인 심리 스킬은 찾지 못했습니다.\n"
            "그래도 사용자의 감정을 충분히 공감해 주고, 일상적인 자기 돌봄 방법(휴식, 식사, 수면, 가벼운 산책 등)을 1~2가지 정도 부드럽게 제안해 주세요.\n"
            "질문을 완전히 멈추기보다는, 사용자가 조금 더 자신의 상황을 설명할 수 있도록 열린 질문을 1개 포함해 주세요."
        )

    # 스킬 목록을 요약해서 모델에 넘김
    lines = ["[내부 심리 스킬 추천 목록]"]
    for s in skills:
        name = s.get("name", "이름 없음")
        cat = s.get("category", "기타")
        desc = s.get("description", "").strip()
        steps = s.get("steps", [])

        lines.append(f"- 스킬 이름: {name} (카테고리: {cat})")
        if desc:
            lines.append(f"  · 개념: {desc}")
        if steps:
            lines.append("  · 간단한 단계:")
            for i, step in enumerate(steps, start=1):
                lines.append(f"    {i}) {step}")

    if force_detail:
        # 동일 문장이 두 번째 이상 들어온 경우 → 스킬 하나를 꼭 풀어서 설명
        lines.append(
            "\n[응답 지침 - 강제 스킬 상세 설명 모드]\n"
            "아래 스킬들 중에서 '사용자의 현재 고민과 가장 잘 맞는 스킬 딱 1개'를 선택해 주세요.\n"
            "응답에서는 다음을 지켜 주세요:\n"
            "1) 먼저 사용자의 감정을 1~2문장 정도로 공감해 주세요.\n"
            "2) 그 다음, 선택한 스킬 이름을 사용자가 이해하기 쉽게 '예를 들면 ~라는 방법이 있어요'처럼 한 번 언급해 주세요.\n"
            "3) 이어서 그 스킬을 실제로 해볼 수 있도록, 핵심 단계 3~4개를 짧고 구체적으로 안내해 주세요.\n"
            "4) 너무 과제처럼 부담스럽지 않게, '괜찮다면', '가볍게 시도해보는 것도 좋다'는 톤으로 제안해 주세요.\n"
            "5) 마지막에는, 사용자가 이 스킬을 해봤을 때 어땠는지 나중에 나눌 수 있도록, 아주 짧은 열린 질문을 1개만 덧붙여 주세요.\n"
            "중요: '스킬', '목록', '내부 정보' 같은 표현은 드러내지 말고, 자연스러운 상담 대화처럼 말해 주세요."
        )
    else:
        # 일반 모드: 1~2개 스킬을 자연스럽게 섞어서 제안
        lines.append(
            "\n[응답 지침 - 일반 모드]\n"
            "아래 스킬들 중에서, 사용자의 상황과 감정에 가장 잘 맞는 스킬 1~2개를 선택해 주세요.\n"
            "응답에서는 다음을 지켜 주세요:\n"
            "1) 먼저 사용자의 감정을 충분히 공감하는 2~3문장을 말해 주세요.\n"
            "2) 그런 다음, 선택한 스킬을 '예를 들면 ~라는 방법도 있어요'처럼 이름을 한 번 정도 언급해 주세요.\n"
            "3) 각 스킬마다 핵심이 되는 단계 2~3개만 간단히 소개해 주세요. (너무 길게 나열하지 마세요.)\n"
            "4) 제안은 어디까지나 선택지로 제시하고, 사용자가 부담 없이 골라볼 수 있는 분위기로 이야기해 주세요.\n"
            "5) 마지막에는, 사용자의 생각이나 경험을 조금 더 들어볼 수 있는 열린 질문을 1개 포함해 주세요.\n"
            "중요: '스킬', '목록', '내부 정보' 같은 표현은 드러내지 말고, 자연스러운 상담 대화처럼 말해 주세요."
        )

    return "\n".join(lines)

# ── 2) LLM 호출(맥락 + SDK 호환 + 429/503 재시도) ───────────────────────
HISTORY_MAX_TURNS = 8
history: List[Dict[str, str]] = []

def make_contents(user_text: str, skills: List[Dict[str, Any]], force_detail: bool) -> List[Dict[str, Any]]:
    """
    SYSTEM 규칙 + 최근 대화 히스토리 + (RAG로 찾은 심리 스킬 정보) + 현재 유저 발화
    를 하나의 컨텍스트로 만들어서 LLM에 넘긴다.
    """
    msgs: List[Dict[str, Any]] = []

    # system_instruction 미지원 SDK 대비: 규칙을 첫 user 메시지로 주입
    msgs.append({"role": "user", "parts": [{"text": f"[시스템 규칙]\n{SYSTEM}"}]})

    # 최근 대화 히스토리
    for m in history[-HISTORY_MAX_TURNS * 2:]:
        msgs.append({
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["text"]}]
        })

    # RAG로 찾은 심리 스킬 정보 (내부용)
    skills_text = format_skills_for_prompt(skills, force_detail)
    msgs.append({"role": "user", "parts": [{"text": skills_text}]})

    # 실제 사용자 발화
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

def safe_generate_content(
    model: str,
    contents: list,
    temperature: float = 0.7,
    max_output_tokens: int = 512,
):
    # 429/503 대비 재시도 (지수 백오프 + 지터)
    attempts = 5
    for i in range(attempts):
        try:
            return _raw_generate(model, contents, temperature, max_output_tokens)
        except (ServerError, ClientError) as e:
            msg = getattr(e, "message", str(e))
            transient = any(
                s in msg
                for s in [
                    "UNAVAILABLE",
                    "RESOURCE_EXHAUSTED",
                    "overloaded",
                    "quota",
                    "temporarily",
                ]
            )
            if i < attempts - 1 and transient:
                sleep = (0.6 * (2 ** i)) + random.uniform(0, 0.3)  # 0.6, 1.2, 2.4, ...
                print(f"⚠️ 재시도 준비({i+1}/{attempts-1})… 잠시 대기: {sleep:.2f}s")
                time.sleep(sleep)
                continue
            raise

def generate_reply(user_text: str, skills: List[Dict[str, Any]], force_detail: bool) -> str:
    """
    최종 답변 생성:
    1) 이미 선택된 skills와 force_detail 플래그를 받아서,
    2) SYSTEM + 히스토리 + 스킬 정보 + 현재 발화를 LLM에 전달.
    """
    try:
        contents = make_contents(user_text, skills, force_detail)
        resp = safe_generate_content(
            MODEL,
            contents,
            temperature=0.7,
            max_output_tokens=512,
        )
        return (getattr(resp, "text", "") or "").strip()
    except ClientError as e:
        msg = getattr(e, "message", str(e))
        if "API key not valid" in msg or "API_KEY_INVALID" in msg:
            return (
                "API 키가 유효하지 않아 응답을 생성할 수 없어요. "
                ".env의 GEMINI_API_KEY가 Google AI Studio에서 발급된 키인지 확인해 주세요."
            )
        return f"모델 호출 중 오류가 발생했어요: {msg}"
    except ServerError as e:
        msg = getattr(e, "message", str(e))
        return (
            f"서버가 혼잡해 응답이 어려워요(일시 오류). 잠시 후 다시 시도해 주세요. 상세: {msg}"
        )
    except Exception as e:
        return f"예상치 못한 오류가 발생했어요: {e}"

# ── 2-1) psybot FastAPI와 통신하는 함수들 ────────────────────────────────
def create_psybot_session(user_id: int = USER_ID) -> int:
    """
    psybot FastAPI에 /sessions 호출해서 세션 하나 만들기
    서버가 안 켜져 있으면 0을 리턴해서, 챗봇은 그냥 로컬로만 동작.
    """
    try:
        resp = requests.post(
            f"{PSYBOT_API}/sessions",
            json={"user_id": user_id},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        sid = int(data["session_id"])
        print(f"🗄 psybot 세션 생성 성공: session_id={sid}")
        return sid
    except Exception as e:
        print(f"⚠️ psybot 세션 생성 실패 (DB 로그는 건너뜀): {e}")
        return 0


def log_psybot_message(session_id: int, text: str, user_id: int = USER_ID):
    """
    /messages 엔드포인트로 사용자 메시지를 psybot DB에 기록
    (분석은 psybot 쪽 analyze()가 알아서 함)
    """
    if session_id <= 0:
        return
    try:
        resp = requests.post(
            f"{PSYBOT_API}/messages",
            json={
                "user_id": user_id,
                "session_id": session_id,
                "text": text,
            },
            timeout=5,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️ psybot 메시지 로그 실패: {e}")

# ── 3) 메인 루프 ───────────────────────────────────────────────────────
LOG_FILE = "chat_logs.jsonl"  # 로그 파일 이름 지정

def main():
    print("👤 사용자에게 '종료' 입력 시 종료됩니다.")

    # psybot 세션 하나 생성 (DB 연동용)
    session_id = create_psybot_session(USER_ID)

    # 동일 문장 반복 체크용
    prev_user: str | None = None
    same_count: int = 0

    while True:
        try:
            user = input("👤 사용자: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🤖 챗봇을 종료합니다.")
            break

        if user.lower() in ["종료", "quit", "exit"]:
            print("🤖 챗봇을 종료합니다.")
            break
        if not user:
            continue

        # DB에 메시지 먼저 기록 시도 (세션 없으면 내부에서 자동 스킵)
        log_psybot_message(session_id, user)

        # 동일 문장 반복 여부 체크
        if prev_user is not None and user == prev_user:
            same_count += 1
        else:
            same_count = 1
            prev_user = user

        # 두 번째 이상 같은 문장이 들어오면 스킬 상세 모드 on
        force_detail = same_count >= 2

        # 위기 여부 먼저 확인 (키워드 기반)
        if is_crisis(user):
            reply = SAFETY_MSG
            used_skills: List[Dict[str, Any]] = []
        else:
            # 위기가 아니면 RAG 기반 심리 스킬 추천 + 답변 생성
            used_skills = select_skills(user)
            reply = generate_reply(user, used_skills, force_detail)

        print("🤖 챗봇:", reply)

        # 대화 히스토리 저장
        history.append({"role": "user", "text": user})
        history.append({"role": "assistant", "text": reply})

        # 로그 저장 (사용된 스킬 정보 + force_detail 여부도 기록)
        try:
            log_entry: Dict[str, Any] = {
                "timestamp": datetime.now().isoformat(),
                "user": user,
                "assistant": reply,
                "same_text_count": same_count,
                "force_detail": force_detail,
            }
            if used_skills:
                log_entry["skills"] = [
                    {
                        "name": s.get("name"),
                        "category": s.get("category"),
                        "keywords": s.get("keywords", []),
                    }
                    for s in used_skills
                ]
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ 로그 저장 실패: {e}")


if __name__ == "__main__":
    main()
