-- DB 만들기
CREATE DATABASE IF NOT EXISTS psy
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE psy;

-- HF 적재용 테이블 (MySQL 버전)
CREATE TABLE IF NOT EXISTS assessments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL DEFAULT 0,
  tool VARCHAR(50) NOT NULL,
  external_id VARCHAR(100) NOT NULL,
  score DECIMAL(6,3) NULL,
  label VARCHAR(50) NULL,
  ts DATETIME(6) NOT NULL,          -- Python datetime ↔ MySQL DATETIME
  data_source VARCHAR(50) NOT NULL,
  version VARCHAR(20) NOT NULL,
  ingested_at DATETIME(6) NOT NULL,

  UNIQUE KEY uk_tool_external (tool, external_id),
  KEY ix_user_ts (user_id, ts)
);
