from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy import text

# 내부 모듈
from .db import get_conn  # SQLite (기존)
# 선택: db.py에서 노출한 MySQL 엔진, Mongo DB 핸들 (없으면 None)
try:
    from .db import engine, mdb
except Exception:
    engine, mdb = None, None

# 분석기
from .analyze import analyze

app = FastAPI(title="PsyBot API")

# =========================
# 기존 SQLite 기반 엔드포인트
# =========================

class MsgIn(BaseModel):
    user_id: int
    text: str
    session_id: int | None = None

class SessionIn(BaseModel):
    user_id: int

@app.post("/sessions")
def create_session(body: SessionIn):
    # UTC 표준 ISO (…Z) 로 저장
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions(user_id, started_at) VALUES (?, ?)",
            (body.user_id, now),
        )
        sid = cur.lastrowid
    return {"session_id": sid, "user_id": body.user_id, "started_at": now}

@app.post("/messages")
def post_message(body: MsgIn):
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    inf = analyze(body.text)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO user_message(user_id, session_id, text, created_at, source, masked)
            VALUES (?, ?, ?, ?, 'chat', 0)
            """,
            (body.user_id, body.session_id, body.text, now),
        )
        msg_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO inference_result(
              message_id, model_name, emotion, sentiment_score, toxicity, risk_flag, inferred_at, valence, arousal
            ) VALUES (?,?,?,?,?,?,?,?,?)
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
            WHERE m.user_id=?
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
        cur.execute(
            "SELECT cue_id, name, modality, description, plausible_neuro, evidence_level, variability, sources "
            "FROM kb_social_cue WHERE name=? LIMIT 1",
            (body.cue_name,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "cue not found")
        (cue_id, name, modality, description, neuro, level, varb, src) = row

        cur.execute(
            "SELECT state_label, valence_hint, arousal_hint, confidence, note FROM cue_interpretation WHERE cue_id=?",
            (cue_id,),
        )
        interps = cur.fetchall()
        cur.execute(
            "SELECT caution_text, severity FROM cue_caution WHERE cue_id=?",
            (cue_id,),
        )
        cauts = cur.fetchall()
        cur.execute(
            "SELECT label, steps, tone, boundaries FROM cue_intervention WHERE cue_id=?",
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
        "interventions": [{"label": l, "steps": st, "tone": tn, "boundaries": b} for (l, st, tn, b) in ivs],
    }

# =========================
# 추가: MySQL / Mongo 조회
# =========================

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

@app.get("/events/recent")
def events_recent(limit: int = 20):
    """
    Mongo(events) 최근 이벤트 조회
    """
    if mdb is None:
        raise HTTPException(500, "Mongo client not configured")
    cur = (
        mdb["events"]
        .find({}, {"_id": 0})
        .sort("ts", -1)
        .limit(int(limit))
    )
    return {"items": list(cur)}

# --- Mongo helpers (추가) ---
from src.mongo import count_events, top_labels

@app.get("/mongo/count")
def mongo_count():
    return {"events": count_events()}

@app.get("/mongo/labels")
def mongo_labels(limit: int = 10):
    return [{"label": d["_id"], "count": d["c"]} for d in top_labels(limit)]
