INSERT IGNORE INTO users(user_id, nickname, consent_at)
VALUES (1, '재용', '2025-11-03 10:00:00');

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

-- 5) 연락 빈도가 눈에 띄게 늘어남
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(105,'연락 빈도가 늘어남','pattern',
 '예전보다 먼저 연락을 자주 보내고, 답장도 빠르게 오는 패턴',
 '보상 기대/사회적 유대 욕구 증가 시 상호작용 빈도↑',
 '중간',
 '성향·스케줄·상황(시험기간, 프로젝트 등)에 따라 크게 달라질 수 있음',
 '메신저 사용 패턴 연구, 연애 관련 설문연구 등');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(105,'호감/관심 상승 가능성', 0.5,0.5,'중간','다른 긍정 시그널(만나자 제안 등)과 같이 볼 것'),
(105,'외로움/심심함 해소용 상호작용', 0.1,0.4,'낮음','여러 명에게 동시에 연락 돌리는 패턴인지 확인 필요');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(105,'단순히 시간이 남거나, 과제가 끝난 시기일 수도 있음. 연락량만으로 확정 해석 금지.','info');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(105,'부담 없는 상호 호감 확인',
 '상대가 자주 먼저 연락할 때, 나도 가볍게 먼저 연락해 보고 대화 길이/반응을 비교 관찰',
 'casual','상대가 답을 짧게 하거나 늦게 하면 연락 빈도를 잠시 줄여 균형 맞추기');

-- 6) 연락 빈도가 눈에 띄게 줄어듦
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(106,'연락 빈도가 줄어듦','pattern',
 '예전보다 답장이 눈에 띄게 느려지거나, 먼저 연락이 거의 오지 않는 패턴',
 '관심/동기 저하, 피로·번아웃, 회피 성향 등에서 상호작용 회피가 늘어날 수 있음',
 '낮음',
 '업무 폭주, 시험기간, 가족 문제 등 외부 요인으로도 쉽게 발생할 수 있음',
 '모바일 사용 패턴 연구, 회피적 애착 관련 연구 등');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(106,'관심 저하/거리 두기 가능성', -0.4,0.3,'중간','몇 주 이상 패턴이 유지되고, 약속 취소·미래 이야기 회피와 함께 나타날 때 의미가 커짐'),
(106,'일시적 스트레스/바쁨', -0.1,0.7,'낮음','기간이 짧고, 직접 만나면 태도가 크게 다르지 않다면 “마음 식음”으로 단정하기 이름');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(106,'연락 빈도 감소만 보고 “마음이 식었다”고 단정하면 관계에 부담을 줄 수 있음. 기간·상황·다른 행동과 반드시 함께 해석할 것.','warn');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(106,'마음 확인보다 컨디션부터 물어보기',
 '1) “요즘 좀 바빠 보여서 걱정됐어요. 많이 힘들어요?”처럼 상태를 먼저 묻기\n2) 상대가 힘들다 하면, 원망 대신 공감 위주로 반응하기\n3) 대화 여유가 생기면 그때 “요즘 우리 연락 패턴은 어떠셨어요?”처럼 부드럽게 이야기 꺼내기',
 'gentle','상대가 짧게만 답하거나 대화를 빨리 마무리하려 하면, 감정 토로·추궁은 뒤로 미루기');

-- 7) 만남/약속을 자주 미루거나 애매하게 넘김
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(107,'만남/약속을 자주 미룸','pattern',
 '예전에는 먼저 보자고 하던 사람이, 요즘은 약속을 자주 미루거나 “나중에 보자” 정도의 애매한 말로 넘김',
 '관계 유지 동기가 떨어지면, 직접 만남·투자 행동을 줄이려는 경향이 생길 수 있음',
 '낮음',
 '체력·금전·시간 문제, 번아웃 등 다른 이유도 흔함',
 '연애/대인관계 설문 연구, 회피 전략 관련 이론');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(107,'관계 투자 의지 감소', -0.5,0.4,'중간','연락 빈도 감소, 미래 계획 회피와 함께 나타날 때 “식어가는 패턴”으로 볼 수 있음'),
(107,'번아웃/자기 여유 부족', -0.2,0.6,'낮음','일·학업·가족 문제 등으로 전반적인 만남 자체가 줄어드는 경우도 많음');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(107,'한두 번 약속 미루는 것만으로 “날 싫어한다”고 해석하면 오해가 커질 수 있음. 최소 몇 번의 패턴과 다른 행동들을 함께 볼 것.','info');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(107,'직접적인 요구보다 선택권을 열어두기',
 '1) “요즘 많이 바쁘면 우리 만나는 속도 조금 천천히 가도 괜찮아요”처럼 압박을 낮춰주고\n2) “당신이 편한 타이밍을 말해주면 그때 맞출게요”처럼 선택권을 넘긴 뒤\n3) 이후에도 계속 피하면, 내 감정을 차분하게 정리해서 솔직히 전달하기',
 'calm','상대가 애매한 말만 계속 반복한다면, 스스로를 지키기 위해 거리 두기를 선택하는 것도 옵션임');

-- 8) 나를 미래 계획에 자주 포함시킴
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(108,'미래 계획에 나를 자주 포함함','verbal',
 '여행, 행사, 방학 계획 등을 이야기할 때 나를 자연스럽게 같이 넣어서 말함(“그때 같이 가자”, “우리도 한 번 해볼래?” 등)',
 '장기적 관계·유대에 대한 동기와 기대가 있을 때, 계획에 상대를 포함시키는 경향',
 '낮음',
 '장난/사교적인 말투일 수도 있어 맥락 확인 필요',
 '연애/관계 설문, 친밀도와 미래 계획의 연관성 연구 일부');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(108,'장기적으로 함께하고 싶은 마음/호감', 0.6,0.4,'중간','실제 행동(약속을 지키는지)과 같이 볼 때 신뢰도↑'),
(108,'가벼운 말버릇·농담', 0.1,0.5,'낮음','여러 사람에게 같은 식으로 말하는지 관찰 필요');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(108,'말로만 미래를 자주 이야기하지만 행동이 전혀 따라오지 않는다면, 말 자체에 너무 큰 의미를 두지 않는 것이 안전함.','info');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(108,'작은 약속부터 현실로 만들어보기',
 '1) 상대가 제안한 미래 계획 중 부담이 적은 것 하나를 골라\n2) “그때 진짜 한 번 해볼까?”처럼 부드럽게 구체화 제안\n3) 일정·비용 등 현실적인 이야기로 이어지는지 지켜보기',
 'casual','상대가 계속 말만 하고 구체화를 회피하면, 장기적인 기대는 너무 앞서가지 않기');

-- 9) 내 SNS를 자주 보고 반응함
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(109,'내 SNS에 자주 반응함','digital',
 '스토리/피드에 좋아요, 이모티콘, 답장을 자주 보내거나, 내가 올린 내용을 대화에서 자주 언급함',
 '관심 대상의 정보에 더 자주 주의를 기울이고, 상호작용 기회를 찾는 경향',
 '낮음',
 'SNS 사용 습관(원래 다수에게 반응 많이 하는 사람인지)에 따라 크게 달라짐',
 'SNS 상호작용과 관계 친밀성 관련 설문연구들');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(109,'관심/호감 + 대화거리 만들기', 0.4,0.5,'중간','오프라인/채팅에서도 나에게만 유독 반응이 많은지 비교 필요'),
(109,'친구로서의 높은 관심/팬심', 0.2,0.5,'낮음','여러 사람에게도 비슷하게 반응한다면 연애감정보다는 친밀감 쪽 가능성');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(109,'SNS 반응은 가벼운 클릭에 불과할 수 있음. 실제 만남·대화에서의 태도와 반드시 함께 볼 것.','info');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(109,'SNS에서 오프라인 대화로 자연스럽게 이어가기',
 '1) 스토리/댓글을 계기로 “이거 진짜 좋아하시나 봐요?”처럼 가벼운 질문 던지기\n2) 공통 관심사가 확인되면 “나중에 이것도 같이 해볼래요?”처럼 작은 제안으로 연결해보기',
 'light','반응은 많은데 만남/대화 제안은 계속 피하면, SNS 반응을 과도하게 해석하지 않기');

-- 10) 감정/사적인 이야기를 피하고 대화를 자주 끊음
INSERT INTO kb_social_cue(cue_id,name,modality,description,plausible_neuro,evidence_level,variability,sources) VALUES
(110,'감정/사적인 얘기를 피함','verbal',
 '예전에는 감정·일상·고민을 꽤 나누던 사람이, 요즘은 “암튼 괜찮아”, “그냥 그래”처럼 감정을 짧게 막고 화제를 자주 바꿈',
 '정서적 친밀감을 줄이거나, 더 깊은 관계로 발전하는 것을 피하고 싶을 때 나타날 수 있는 회피 패턴',
 '낮음',
 '원래 감정을 말로 풀기 어려운 성향일 수도 있고, 특정 주제(가족/트라우마 등)를 피하는 것일 수도 있음',
 '애착/회피 전략 관련 연구에서 일부 보고');

INSERT INTO cue_interpretation(cue_id,state_label,valence_hint,arousal_hint,confidence,note) VALUES
(110,'정서적 거리두기/관계 깊이 조절', -0.4,0.4,'중간','연락 빈도·만남 빈도 감소와 함께라면 “식어가는 신호”일 가능성↑'),
(110,'일시적 방어/에너지 부족', -0.1,0.6,'낮음','지치거나 예민한 시기엔 누구에게나 나타날 수 있는 방어 반응');

INSERT INTO cue_caution(cue_id,caution_text,severity) VALUES
(110,'감정 표현 감소를 곧바로 “나에 대한 관심 상실”로 해석하기보다, 자존감·우울감·스트레스 문제 가능성도 함께 고려할 것.','warn');

INSERT INTO cue_intervention(cue_id,label,steps,tone,boundaries) VALUES
(110,'감정을 캐묻기보다 안전한 공간이라는 메시지 주기',
 '1) “꼭 말 안 해도 돼요. 그냥 힘들면 힘들다고만 말해줘도 괜찮아요.”처럼 표현의 기준을 낮춰주고\n2) “내 앞에서는 괜찮은 척 안 해도 된다는 것만 알아줬으면 좋겠어.” 같은 한 마디를 남기기\n3) 이후에도 계속 벽을 느낀다면, 나도 과도하게 매달리기보다 내 감정도 지키는 선을 만들기',
 'warm','상대가 명확히 “이런 얘기는 하고 싶지 않다”고 말했을 땐 더 이상 캐묻지 않기');

