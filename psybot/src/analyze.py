from dataclasses import dataclass
from datetime import datetime

NEG_WORDS = ["힘들", "피곤", "우울", "짜증", "불안", "죽고", "자살"]
POS_WORDS = ["좋", "행복", "기쁨", "설렘", "뿌듯"]
ANXIETY_WORDS = ["불안", "초조", "두근", "심장이", "긴장"]

@dataclass
class Inference:
    emotion: str
    sentiment_score: float
    toxicity: float
    risk_flag: str
    valence: float
    arousal: float
    model_name: str = "rule-ko-sentiment"
    inferred_at: str = datetime.utcnow().isoformat(timespec="seconds") + "Z"

def analyze(text: str) -> Inference:
    t = text.lower()
    score = 0.0
    if any(w in t for w in POS_WORDS):
        score += 0.6
    if any(w in t for w in NEG_WORDS):
        score -= 0.7

    if any(w in t for w in ANXIETY_WORDS):
        emotion = "anxiety"
    elif score > 0.2:
        emotion = "joy"
    elif score < -0.2:
        emotion = "sadness"
    else:
        emotion = "neutral"

    if emotion == "anxiety":
        valence, arousal = -0.5, 0.8
    elif emotion == "sadness":
        valence, arousal = -0.6, 0.2
    elif emotion == "joy":
        valence, arousal = 0.6, 0.8
    else:
        valence, arousal = 0.0, 0.4

    risk = "self_harm_hint" if ("자살" in t or "죽고" in t) else "none"

    return Inference(
        emotion=emotion,
        sentiment_score=score,
        toxicity=0.0,
        risk_flag=risk,
        valence=valence,
        arousal=arousal
    )
