import uuid

IMPACT = {"critical": 3, "warning": 2, "info": 1}


def build_recommendations(rule_results: list[dict]) -> list[dict]:
    recs = []
    for item in rule_results:
        rule, passed = item["rule"], item["passed"]
        if passed:
            continue
        recs.append({
            "id": str(uuid.uuid4())[:8],
            "title": rule.title,
            "category": rule.category,
            "severity": rule.severity,
            "priority_score": IMPACT.get(rule.severity, 1) * rule.weight,
            "description": rule.description,
            "fix": rule.fix,
        })
    recs.sort(key=lambda r: r["priority_score"], reverse=True)
    return recs
