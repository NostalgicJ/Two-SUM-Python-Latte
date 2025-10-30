const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const messages = document.getElementById('messages');

// 최초 봇 인사 (피드에 표시)
appendBot(`Welcome to EmotAI.\nThe first step to understanding your emotions begins here.`);

// 엔터/버튼 제출
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendUser(text);
  input.value = '';
  input.focus();

  // 실제 API 붙이기 전 모의 답변 (규칙 기반)
  const reply = localRuleBasedReply(text);

  // "생각 중..." 느낌 주기
  const thinkingEl = appendBot('…');
  await sleep(350); // 작은 딜레이
  thinkingEl.remove();

  appendBot(reply);

  // 실제 백엔드가 있으면 아래처럼:
  // const reply = await callChatApi(text);
  // appendBot(reply);
});

// 유틸: 메시지 추가
function appendUser(text)  { return appendMsg(text, 'user'); }
function appendBot(text)   { return appendMsg(text, 'bot'); }
function appendMsg(text, who) {
  const el = document.createElement('div');
  el.className = `msg ${who}`;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight; // 자동 스크롤
  return el;
}

// 아주 간단한 규칙(데모용)
function localRuleBasedReply(text) {
  const t = text.toLowerCase();
  if (/[슬프|우울|sad|down]/.test(t)) {
    return "그 감정 충분히 이해돼. 지금 마음을 1~10 숫자로 표현해볼래? 그 숫자에 맞춰 아주 작은 실천을 같이 정해보자.";
  }
  if (/[불안|anx|걱정]/.test(t)) {
    return "불안을 느낄 때 4-4-6 호흡(4초 들숨, 4초 머금기, 6초 날숨)을 3회 시도해봐. 그리고 불안을 만드는 생각을 한 문장으로 적어볼래?";
  }
  if (/[행복|기뻐|happy|good]/.test(t)) {
    return "좋다! 그 행복의 원인을 적어보자. 나중에 필요할 때 꺼내볼 수 있는 너만의 자원이 돼.";
  }
  return "고마워. 방금 메시지에서 핵심 감정 한 단어를 고른다면 뭐일까? 그 단어를 적어줘.";
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// 실제 API 예시 (백엔드 있을 때 사용)
async function callChatApi(userText) {
  const resp = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userText })
  });
  const data = await resp.json();
  return data.reply || '응답을 가져오지 못했어.';
}
