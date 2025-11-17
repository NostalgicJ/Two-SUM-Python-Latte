-- MySQL용 스키마
-- DB는 init_db.py에서 psy 라는 이름으로 생성/USE 함

-- 1) 사용자
CREATE TABLE IF NOT EXISTS users (
  user_id     INT           NOT NULL PRIMARY KEY,
  nickname    VARCHAR(50)   NOT NULL,
  consent_at  DATETIME      NULL,
  is_active   TINYINT(1)    NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2) 세션 (채팅 세션)
CREATE TABLE IF NOT EXISTS sessions (
  session_id  INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT           NOT NULL,
  started_at  DATETIME      NOT NULL,
  ended_at    DATETIME      NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3) 메시지 (대화 로그)
CREATE TABLE IF NOT EXISTS messages (
  message_id  INT AUTO_INCREMENT PRIMARY KEY,
  session_id  INT           NOT NULL,
  role        ENUM('user','assistant','system') NOT NULL,
  content     TEXT          NOT NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4) 사회적 단서 마스터 테이블
CREATE TABLE IF NOT EXISTS kb_social_cue (
  cue_id          INT           NOT NULL PRIMARY KEY,
  name            VARCHAR(100)  NOT NULL,
  modality        VARCHAR(50)   NOT NULL,
  description     TEXT          NOT NULL,
  plausible_neuro TEXT          NULL,
  evidence_level  VARCHAR(20)   NULL,
  variability     TEXT          NULL,
  sources         TEXT          NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5) 단서 해석 테이블
CREATE TABLE IF NOT EXISTS cue_interpretation (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  cue_id        INT           NOT NULL,
  state_label   VARCHAR(255)  NOT NULL,
  valence_hint  FLOAT         NULL,
  arousal_hint  FLOAT         NULL,
  confidence    VARCHAR(20)   NULL,
  note          TEXT          NULL,
  FOREIGN KEY (cue_id) REFERENCES kb_social_cue(cue_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6) 주의/주의사항 테이블
CREATE TABLE IF NOT EXISTS cue_caution (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  cue_id       INT           NOT NULL,
  caution_text TEXT          NOT NULL,
  severity     VARCHAR(20)   NULL,
  FOREIGN KEY (cue_id) REFERENCES kb_social_cue(cue_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7) 개입/대응 전략 테이블
CREATE TABLE IF NOT EXISTS cue_intervention (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  cue_id    INT           NOT NULL,
  label     VARCHAR(100)  NOT NULL,
  steps     TEXT          NOT NULL,
  tone      VARCHAR(50)   NULL,
  boundaries TEXT         NULL,
  FOREIGN KEY (cue_id) REFERENCES kb_social_cue(cue_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
