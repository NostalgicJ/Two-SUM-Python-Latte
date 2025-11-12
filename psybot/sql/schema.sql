PRAGMA foreign_keys = ON;

-- 1) 사용자
CREATE TABLE IF NOT EXISTS users (
  user_id     INTEGER PRIMARY KEY,
  nickname    TEXT,
  consent_at  TEXT,
  is_active   INTEGER DEFAULT 1
);

-- 2) 세션
CREATE TABLE IF NOT EXISTS sessions (
  session_id  INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL,
  started_at  TEXT NOT NULL,
  ended_at    TEXT,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3) 원문 메시지
CREATE TABLE IF NOT EXISTS user_message (
  message_id  INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL,
  session_id  INTEGER,
  text        TEXT NOT NULL,
  lang        TEXT DEFAULT 'ko',
  created_at  TEXT NOT NULL,
  source      TEXT DEFAULT 'chat',
  masked      INTEGER DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 4) 추론 결과 (valence/arousal 포함)
CREATE TABLE IF NOT EXISTS inference_result (
  inference_id    INTEGER PRIMARY KEY,
  message_id      INTEGER NOT NULL UNIQUE,
  model_name      TEXT NOT NULL,
  emotion         TEXT,
  sentiment_score REAL,
  toxicity        REAL,
  risk_flag       TEXT DEFAULT 'none',
  inferred_at     TEXT NOT NULL,
  valence         REAL,
  arousal         REAL,
  FOREIGN KEY (message_id) REFERENCES user_message(message_id)
);

-- 5) (선택) 일별 집계
CREATE TABLE IF NOT EXISTS user_daily_agg (
  user_id       INTEGER NOT NULL,
  date          TEXT NOT NULL,
  msg_cnt       INTEGER DEFAULT 0,
  pos_ratio     REAL,
  neg_ratio     REAL,
  neu_ratio     REAL,
  top_emotion   TEXT,
  avg_sentiment REAL,
  risk_count    INTEGER DEFAULT 0,
  PRIMARY KEY (user_id, date),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 6) (선택) 스냅샷
CREATE TABLE IF NOT EXISTS user_features (
  user_id              INTEGER PRIMARY KEY,
  last_emotion         TEXT,
  last_sentiment       REAL,
  last_message_at      TEXT,
  streak_negative_days INTEGER DEFAULT 0,
  sad_ratio_7d         REAL,
  risk_recent          INTEGER DEFAULT 0,
  updated_at           TEXT,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 관찰 신호(행동/제스처/말투 등)
CREATE TABLE IF NOT EXISTS kb_social_cue (
  cue_id        INTEGER PRIMARY KEY,
  name          TEXT NOT NULL,          -- 예: '머리를 귀 뒤로 넘김'
  modality      TEXT NOT NULL,          -- 'gesture','posture','facial','verbal','digital'
  description   TEXT NOT NULL,          -- 관찰되는 형태
  plausible_neuro TEXT,                 -- 관련 뇌과학/생리 설명(있다면)
  evidence_level TEXT NOT NULL,         -- '높음','중간','낮음'
  variability   TEXT,                   -- 문화/개인차/상황 변동성
  sources       TEXT                    -- 참고 근거 요약(서지/링크 텍스트)
);

-- 신호 → 해석 후보(다의적 가능성 저장)
CREATE TABLE IF NOT EXISTS cue_interpretation (
  interp_id     INTEGER PRIMARY KEY,
  cue_id        INTEGER NOT NULL,
  state_label   TEXT NOT NULL,          -- 예: '호감 가능성 ↑', '불안/긴장', '피로'
  valence_hint  REAL,                   -- -1..1 (대략적 힌트)
  arousal_hint  REAL,                   -- 0..1  (대략적 힌트)
  confidence    TEXT NOT NULL,          -- '낮음','중간','높음' (해석 신뢰)
  note          TEXT,                   -- 언제 그런 경향이 있는지
  FOREIGN KEY (cue_id) REFERENCES kb_social_cue(cue_id)
);

-- 오해 방지용 주의/금기
CREATE TABLE IF NOT EXISTS cue_caution (
  caution_id    INTEGER PRIMARY KEY,
  cue_id        INTEGER NOT NULL,
  caution_text  TEXT NOT NULL,          -- “습관/머리 고정하려는 동작일 수 있음” 등
  severity      TEXT DEFAULT 'info',     -- 'info','warn','critical'
  FOREIGN KEY (cue_id) REFERENCES kb_social_cue(cue_id)
);

-- 대응 제안(상담/대화 기술)
CREATE TABLE IF NOT EXISTS cue_intervention (
  iv_id         INTEGER PRIMARY KEY,
  cue_id        INTEGER NOT NULL,
  label         TEXT NOT NULL,          -- '오픈 질문으로 확인'
  steps         TEXT NOT NULL,          -- 구체 대화 스크립트
  tone          TEXT DEFAULT 'gentle',  -- 'gentle','direct','playful'
  boundaries    TEXT,                   -- 경계 존중 안내
  FOREIGN KEY (cue_id) REFERENCES kb_social_cue(cue_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_msg_user_time ON user_message(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_inf_msg ON inference_result(message_id);
