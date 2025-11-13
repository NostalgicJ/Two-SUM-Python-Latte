import uvicorn  # FastAPI를 실행하기 위한 ASGI 서버
from fastapi import FastAPI
from pydantic import BaseModel # Flask의 request.json 대신 사용 (타입 검증용)

# chatbot.py에서 리팩토링한 함수들을 가져옵니다.
from chatbot import get_bot_response, log_conversation, HISTORY_MAX_TURNS

# 1. FastAPI 앱 인스턴스 생성
app = FastAPI()

# 2. Pydantic 모델 정의
# - 이것이 FastAPI의 핵심입니다.
# - 클라이언트가 보내야 할 JSON의 '설계도'를 정의합니다.
# - 이 형태에 맞지 않는 요청이 오면, FastAPI가 자동으로 422 오류를 반환해 줍니다.
class ChatRequest(BaseModel):
    user_id: str
    message: str

# [중요] 임시 대화 내역 저장소 (Flask 예제와 동일)
# ---------------------------------------------
# 실제 서비스에서는 이 부분이 Redis나 DB로 대체되어야 합니다.
chat_histories: dict[str, list[dict[str, str]]] = {}
# ---------------------------------------------


# 3. API 엔드포인트 생성
# @app.route() 대신 @app.post()를 사용합니다.
@app.post("/chat")
async def handle_chat(request_data: ChatRequest):
    """
    메인 채팅 API 엔드포인트
    
    FastAPI는 request_data: ChatRequest 타입 힌트를 보고
    - 1. 요청 바디가 JSON인지 확인
    - 2. JSON 안에 user_id와 message가 있는지 확인
    - 3. user_id가 문자열(str)인지, message가 문자열(str)인지 확인
    이 모든 것을 '자동'으로 처리하고, request_data 객체에 넣어줍니다.
    """
    
    # 4. Pydantic이 검증해준 데이터 사용
    user_id = request_data.user_id
    user_message = request_data.message.strip()

    if not user_message:
        # FastAPI는 딕셔너리를 반환하면 자동으로 JSON으로 변환합니다.
        # (jsonify()가 필요 없음)
        return {"reply": "메시지를 입력해 주세요."}

    # 5. 이 사용자의 대화 내역(history) 불러오기
    session_history = chat_histories.get(user_id, [])

    # 6. chatbot.py의 메인 함수 호출
    # (참고: get_bot_response가 동기 함수(def)라도 
    #  async def 엔드포인트에서 호출 가능합니다.)
    reply = get_bot_response(user_message, session_history)

    # 7. 새 대화 내용을 임시 DB(chat_histories)에 저장
    session_history.append({"role": "user", "text": user_message})
    session_history.append({"role": "model", "text": reply})

    # 8. 메모리 관리를 위해 오래된 내역 자르기
    if len(session_history) > (HISTORY_MAX_TURNS + 2) * 2:
        session_history = session_history[2:]

    # 9. 갱신된 내역을 다시 저장
    chat_histories[user_id] = session_history
    
    # 10. 파일 로그(JSONL) 남기기 (선택 사항)
    log_conversation(user_message, reply, user_id=user_id)

    # 11. 사용자에게 딕셔너리 형태로 응답 반환 (자동 JSON 변환)
    return {"reply": reply}

# 4. 자동 API 문서 확인용 엔드포인트 (테스트용)
@app.get("/")
async def root():
    return {"message": "챗봇 서버가 실행 중입니다. /docs 로 이동하여 API 문서를 확인하세요."}


# 5. 서버 실행 (Flask의 app.run() 대신 uvicorn 사용)
if __name__ == "__main__":
    print("🤖 FastAPI 챗봇 서버를 시작합니다. (http://127.0.0.1:8000)")
    # uvicorn.run()의 첫 인자는 "파일명:앱객체명" 형태의 문자열입니다.
    uvicorn.run("server_fastapi:app", host="127.0.0.1", port=8000, reload=True)