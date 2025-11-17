from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy import text

# 내부 모듈
from .db import get_conn  # 이제 MySQL 커넥션
# 선택: db.py에서 노출한 MySQL 엔진, Mongo DB 핸들 (없으면 None)
try:
    from .db import engine, mdb
except Exception:
    engine, mdb = None, None

# 분석기
from .analyze import analyze

app = FastAPI(title="PsyBot API")

# =========================
# 공통 유틸: 시간 포맷
# =========================

def now_utc_pair():
    """
    DB에 넣을 DATETIME 문자열 / API 응답용 ISO 문자열을 동시에 만들어줌
    """
    now = datetime.now(timezone.utc).replace(microsecond=0)
    db_value = now.strftime("%Y-%m-%d %H:%M:%S")      # MySQL DATETIME 포맷
    iso_value = now.isoformat().replace("+00:00", "Z")  # 응답용
    return db_value, iso_value

# =========================
# 기존 SQLite 기반 엔드포인트 → MySQL로 변경
# =========================

class MsgIn(BaseModel):
    user_id: int
    text: str
    session_id: int | None = None

class SessionIn(BaseModel):
    user_id: int

@app.post("/sessions")
def create_session(body: SessionIn):
    db_now, iso_now = now_utc_pair()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions(user_id, started_at) VALUES (%s, %s)",
            (body.user_id, db_now),
        )
        sid = cur.lastrowid
    return {"session_id": sid, "user_id": body.user_id, "started_at": iso_now}

@app.post("/messages")
def post_message(body: MsgIn):
    db_now, _ = now_utc_pair()
    inf = analyze(body.text)
    with get_conn() as conn:
        cur = conn.cursor()

        # 1) 원문 메시지 저장
        cur.execute(
            """
            INSERT INTO user_message(user_id, session_id, text, created_at, source, masked)
            VALUES (%s, %s, %s, %s, 'chat', 0)
            """,
            (body.user_id, body.session_id, body.text, db_now),
        )
        msg_id = cur.lastrowid

        # 2) 분석 결과 저장
        cur.execute(
            """
            INSERT INTO inference_result(
              message_id, model_name, emotion, sentiment_score, toxicity, risk_flag, inferred_at, valence, arousal
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                msg_id,
                inf.model_name,
                inf.emotion,
                inf.sentiment_score,
                inf.toxicity,
                inf.risk_flag,
                inf.inferred_at,
                inf.valence,
                inf.arousal,
            ),
        )
    return {"message_id": msg_id, "inference": inf.__dict__}

@app.get("/features/{user_id}")
def get_features(user_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.emotion, r.sentiment_score, r.valence, r.arousal, m.created_at
            FROM user_message m
            JOIN inference_result r ON r.message_id=m.message_id
            WHERE m.user_id=%s
            ORDER BY m.created_at DESC
            LIMIT 5
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    if not rows:
        raise HTTPException(404, "no messages")
    last5 = [
        {"emotion": e, "sentiment": s, "valence": v, "arousal": a, "at": t}
        for (e, s, v, a, t) in rows
    ]
    return {"user_id": user_id, "last5": last5}

class CueIn(BaseModel):
    cue_name: str

@app.post("/cue_explain")
def cue_explain(body: CueIn):
    with get_conn() as conn:
        cur = conn.cursor()

        # 1) cue 마스터
        cur.execute(
            """
            SELECT cue_id, name, modality, description, plausible_neuro, evidence_level, variability, sources
            FROM kb_social_cue
            WHERE name=%s
            LIMIT 1
            """,
            (body.cue_name,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "cue not found")
        (cue_id, name, modality, description, neuro, level, varb, src) = row

        # 2) 해석 리스트
        cur.execute(
            "SELECT state_label, valence_hint, arousal_hint, confidence, note FROM cue_interpretation WHERE cue_id=%s",
            (cue_id,),
        )
        interps = cur.fetchall()

        # 3) 주의사항
        cur.execute(
            "SELECT caution_text, severity FROM cue_caution WHERE cue_id=%s",
            (cue_id,),
        )
        cauts = cur.fetchall()

        # 4) 개입 전략
        cur.execute(
            "SELECT label, steps, tone, boundaries FROM cue_intervention WHERE cue_id=%s",
            (cue_id,),
        )
        ivs = cur.fetchall()

    return {
        "cue": {
            "name": name,
            "modality": modality,
            "description": description,
            "neuro": neuro,
            "evidence": level,
            "variability": varb,
            "sources": src,
        },
        "interpretations": [
            {"label": s, "valence": v, "arousal": a, "confidence": c, "note": n}
            for (s, v, a, c, n) in interps
        ],
        "cautions": [{"text": t, "severity": sev} for (t, sev) in cauts],
        "interventions": [
            {"label": l, "steps": st, "tone": tn, "boundaries": b}
            for (l, st, tn, b) in ivs
        ],
    }

@app.get("/stats/labels")
def stats_labels():
    """
    MySQL(assessments) 라벨별 카운트 조회
    """
    if engine is None:
        raise HTTPException(500, "MySQL engine not configured")
    sql = """
        SELECT label, COUNT(*) AS c
        FROM assessments
        GROUP BY label
        ORDER BY c DESC
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return {"items": rows}