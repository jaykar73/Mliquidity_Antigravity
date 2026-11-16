"""
Sentiment backend functions — CNN Fear & Greed 지수, 7개 구성요소, 최근 3개월 추이.
mybatis-mapper2sql + sqlite3 연동.
"""
from utils.db_helper import fetch_all, load_mapper

load_mapper("sqls/sentiment.xml")


def _score_to_label(score: float | int) -> str:
    s = float(score or 50)
    if s <= 25:
        return "극단적 공포"
    if s <= 45:
        return "공포"
    if s <= 55:
        return "중립"
    if s <= 75:
        return "탐욕"
    return "극단적 탐욕"


def get_fear_greed_score() -> dict:
    """최신 CNN Fear & Greed 점수 및 1주 전 점수 조회."""
    rows = fetch_all(namespace="sentiment", sql_id="selectFearGreedScore", params={})
    if not rows:
        return {"score": 22, "label": "극단적 공포", "prev_score": 28, "observation_date": "2026-11-06"}
    score = int(round(float(rows[0]["score"])))
    prev_score = int(round(float(rows[-1]["score"]))) if len(rows) > 1 else 28
    return {
        "score": score,
        "label": _score_to_label(score),
        "prev_score": prev_score,
        "observation_date": rows[0]["observation_date"],
    }


def get_fear_greed_components() -> list[dict]:
    """CNN Fear & Greed 7개 구성요소 조회."""
    rows = fetch_all(namespace="sentiment", sql_id="selectFGComponents", params={})
    if not rows:
        return [
            {"name": "시장 모멘텀",    "score": 8,  "label": "극단적 공포"},
            {"name": "주가 강도",      "score": 42, "label": "공포"},
            {"name": "시장 폭",        "score": 45, "label": "공포"},
            {"name": "풋/콜 옵션",     "score": 13, "label": "극단적 공포"},
            {"name": "변동성 (VIX)",   "score": 9,  "label": "극단적 공포"},
            {"name": "정크본드 수요",  "score": 36, "label": "공포"},
            {"name": "안전자산 수요",  "score": 1,  "label": "극단적 공포"},
        ]
    result = []
    for r in rows:
        val = int(round(float(r["value"])))
        result.append({
            "code": r["code"],
            "name": r["name"],
            "score": val,
            "label": _score_to_label(val),
        })
    return result


def get_fear_greed_history() -> dict:
    """최근 3개월 CNN Fear & Greed 일별 추이 조회."""
    rows = fetch_all(namespace="sentiment", sql_id="selectFGTrend", params={})
    dates = [r["observation_date"][5:] for r in rows]  # MM-DD
    scores = [int(round(float(r["score"]))) for r in rows]
    return {"dates": dates, "scores": scores}


# 하위 호환 별칭
get_fg_components = get_fear_greed_components
get_fg_trend = get_fear_greed_history
