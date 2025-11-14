# Run
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # 또는 직접 .env 생성: DB_PATH=./psybot.db
python src/init_db.py
uvicorn src.app:app --reload  # http://127.0.0.1:8000/docs