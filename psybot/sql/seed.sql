INSERT OR IGNORE INTO users(user_id, nickname, consent_at)
VALUES (1, '재용', '2025-11-03T10:00:00Z');

-- 1) 머리를 귀 뒤로 넘김
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(101,'머리를 귀 뒤로 넘김','gesture',
 '상대가 대화 중 머리카락을 귀 뒤로 빗어 넘김',
 '자율신경 각성 시 체위/정돈 행동이 늘 수 있음(불편 완화, 자기정돈)',
 '낮음',
 '머리 방해 제거/습관/초점 이동/위생적 이유 등 대안설명 多',
 '대중심리서/관찰연구 혼재: 해석 신뢰 낮음');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(101,'호감 가능성(상대에 더 또렷이 보이려는 정돈행동)', 0.2,0.5,'낮음','다른 긍정 신호와 동반될 때만 보조지표'),
(101,'긴장/불안 완화의 자기정돈행동', -0.1,0.6,'중간','면접/낯선 상황에서 흔함');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(101,'외모 정돈/시야확보/습관일 가능성이 큼. 독립적 지표로 해석 금지.','warn');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(101,'안전한 확인 질문',
 '“여기 조금 덥죠? 자리 불편하진 않으세요?” → “대화 주제 어떤 게 편하세요?”처럼 컨디션/선호를 먼저 묻기',
 'gentle','불편 신호면 즉시 주제/환경 조정');

-- 2) 시선 접촉(지속적)
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(102,'지속적 시선 접촉','facial',
 '상대가 평균보다 오래 눈을 맞춤',
 '사회적 보상/관심 증가 시 시선교환 빈도↑ 가능',
 '중간',
 '문화/개인차 큼(직접 눈맞춤이 불편한 문화도 있음)',
 '사회심리 메타분석 다수(맥락 의존)');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(102,'관심/호감 가능성', 0.4,0.5,'중간','미소/몸 기울임 등 동반 시 강화'),
(102,'권위/평가/도전', -0.1,0.6,'낮음','표정·거리·목소리 톤과 함께 판단');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(102,'응시 지속은 불편·감시로 해석될 수도 있음','info');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(102,'오픈형 대화 확장',
 '“이 주제 꽤 흥미로우신가 봐요? 어떤 점이 좋으셨어요?” 같은 자율적 확장 질문',
 'gentle','상대의 단호한 짧은 답변/시선 회피 시 즉시 강도 낮춤');

-- 3) 몸을 기울임(lean-in)
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(103,'앞으로 몸을 기울임','posture',
 '상체가 상대 쪽으로 기울어 있음',
 '접근 동기↑/주의집중↑ 시 전경화',
 '중간',
 '좌석 배치/소음/청취 문제 등 물리적 요인 가능',
 '환경요인 통제 필요');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(103,'관심/참여도 상승', 0.4,0.5,'중간','고개 끄덕임/미소 동반 시 강화');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(103,'물리적 환경 탓일 수 있음(소음/거리)','info');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(103,'상호성 테스트(가벼운 self-disclosure)',
 '“저는 이런 점이 재미있더라구요. (잠시 멈춤) 상대는 어때요?” 식으로 짧게 나누고 반응을 체크',
 'gentle','사생활 질문은 1단계 낮게 시작');

-- 4) 발끝/몸통 방향(오리엔테이션)
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(104,'발끝/몸통 방향','posture',
 '발끝·배꼽이 향하는 방향이 상호작용 대상과 일치',
 '주의 초점/공간적 접근성 신호',
 '낮음',
 '군중/좌석제약 영향 큼',
 '관찰연구 혼재');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(104,'관심 대상 쪽 정렬', 0.2,0.4,'낮음','다른 지표 동반 시만 보조');
