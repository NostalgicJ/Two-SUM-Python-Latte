// app.js — EmotAI 웹 클라이언트

// ✅ 백엔드 주소 설정
// 같은 도메인(ngrok로 접속한 그 주소) 기준으로 /chat 을 호출하게 함
// 예: https://~~~.ngrok-free.dev/chat
const API_BASE = "";

// DOM 요소 잡기
const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const messages = document.getElementById('messages');

// 최초 봇 인사
appendBot(
  "안녕하세요! 저는 당신의 감정 패턴을 분석하고 이해를 돕는 EmotAI입니다. " +
  "오늘 있었던 일이나 요즘 계속 떠오르는 생각들을 편하게 들려줘."
);

// 폼 제출(엔터 / 버튼 클릭)
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  // 내 메시지 출력
  appendUser(text);
  input.value = '';
  input.focus();

  // "생각 중..." 표시
  const thinkingEl = appendBot('…');

  try {
    // 🔗 백엔드(web_api.py) 호출
    const reply = await callChatApi(text);

    // 생각 중 제거 후 답변 출력
    thinkingEl.remove();
    appendBot(reply);
  } catch (err) {
    console.error('API 호출 오류:', err);
    thinkingEl.remove();
    appendBot('서버와 통신 중 문제가 생겼어. 잠시 후 다시 시도해줘.');
  }
});

// ===== 유틸 함수들 =====

function appendUser(text) {
  return appendMsg(text, 'user');
}

function appendBot(text) {
  return appendMsg(text, 'bot');
}

function appendMsg(text, who) {
  const el = document.createElement('div');
  el.className = `msg ${who}`;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight; // 맨 아래로 스크롤
  return el;
}

// ===== 실제 API 호출 =====
async function callChatApi(userText) {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userText }),
  });

  if (!resp.ok) {
    const errText = await resp.text().catch(() => '');
    throw new Error(`HTTP ${resp.status} ${errText}`);
  }

  const data = await resp.json();
  return data.reply || '응답을 가져오지 못했어.';
}
