// app.js — 웹 프론트에서 FastAPI(웹 챗봇 서버)로 연결

const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const messages = document.getElementById('messages');

// 백엔드 주소 (웹 챗봇 서버)
const API_BASE = 'http://127.0.0.1:8010';

// 최초 봇 인사
appendBot(
  '안녕하세요! 저는 당신의 감정 패턴을 분석하고 이해를 돕는 EmotAI입니다. ' +
  '오늘 당신의 일상 속 이야기를 편하게 들려줘.'
);

// 엔터/버튼 제출
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendUser(text);
  input.value = '';
  input.focus();

  // "생각 중..." 말풍선
  const thinkingEl = appendBot('…');
  try {
    const reply = await callChatApi(text);
    thinkingEl.remove();
    appendBot(reply);
  } catch (err) {
    console.error(err);
    thinkingEl.remove();
    appendBot('지금 서버와 연결이 잘 안 돼. 잠시 뒤에 다시 시도해줄래?');
  }
});

// 유틸: 메시지 추가
function appendUser(text)  { return appendMsg(text, 'user'); }
function appendBot(text)   { return appendMsg(text, 'bot'); }

function appendMsg(text, who) {
  const el = document.createElement('div');
  el.className = `msg ${who}`;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}

// 실제 API 호출
async function callChatApi(userText) {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userText })
  });

  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }
  const data = await resp.json();
  // FastAPI에서 { "reply": "..." } 형태로 줄 거라 가정
  return data.reply || '응답을 가져오지 못했어.';
}
