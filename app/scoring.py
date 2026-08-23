from app.rule_engine import CATEGORIES

CATEGORY_WEIGHTS = {
    "AI Crawlability": 0.25,
    "Structured Data": 0.25,
    "Content Clarity": 0.30,
    "Trust Signals": 0.10,
    "Technical Basics": 0.10,
}


def compute_geo_score(category_scores: dict) -> int:
    total = 0.0
    for c in CATEGORIES:
        total += CATEGORY_WEIGHTS.get(c, 0) * category_scores.get(c, 0)
    return round(total)


def score_label(score: int) -> str:
    if score >= 85:
        return "AI-Ready"
    if score >= 60:
        return "Good Shape"
    if score >= 35:
        return "Needs Work"
    return "Invisible to AI"
