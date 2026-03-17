import os
import json
from datetime import datetime, timedelta
from typing import List, Dict

# =========================
# CONFIG
# =========================

ENRICHED_DIR = "data/enriched"
OUTPUT_DIR = "data/outputs"
TOP_N = 10
DAYS_BACK = 7  # weekly window

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# LOAD DATA
# =========================

def load_enriched_items() -> List[Dict]:
    items = []

    for filename in os.listdir(ENRICHED_DIR):
        if not filename.endswith(".json"):
            continue

        path = os.path.join(ENRICHED_DIR, filename)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items.append(data)
        except Exception as e:
            print(f"[WARN] Failed to load {filename}: {e}")

    return items


# =========================
# DATE FILTER (WEEKLY WINDOW)
# =========================

def is_within_window(item: Dict) -> bool:
    try:
        published = item.get("published_at")
        if not published:
            return True

        try:
            dt = datetime.fromisoformat(published)
        except Exception:
            dt = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %Z")

        cutoff = datetime.utcnow() - timedelta(days=DAYS_BACK)
        return dt >= cutoff

    except Exception:
        return True


# =========================
# FILTER SIGNALS
# =========================

def filter_signals(items: List[Dict]) -> List[Dict]:
    results = []

    for item in items:
        analysis = item.get("analysis", {})
        decision = analysis.get("decision")

        if decision not in ["monitor", "shortlist"]:
            continue

        if not is_within_window(item):
            continue

        results.append(item)

    return results


# =========================
# SCORING FUNCTION
# =========================

def compute_score(item: Dict) -> float:
    analysis = item.get("analysis", {})

    decision = analysis.get("decision", "ignore")
    time_horizon = analysis.get("time_horizon", "archival")
    confidence = analysis.get("confidence", 0.5)

    decision_weight = {
        "monitor": 0.4,
        "shortlist": 0.8,
    }.get(decision, 0.0)

    time_weight = {
        "immediate": 1.0,
        "near_term": 0.9,
        "long_term": 0.75,
        "archival": 0.3,
    }.get(time_horizon, 0.5)

    score = round(decision_weight * time_weight * confidence, 4)
    return score


# =========================
# RANKING
# =========================

def rank_signals(items: List[Dict]) -> List[Dict]:
    ranked = []

    for item in items:
        analysis = item.get("analysis", {})
        score = compute_score(item)

        ranked.append({
            "doc_id": item.get("doc_id"),
            "title": item.get("title"),
            "url": item.get("url"),
            "published_at": item.get("published_at"),
            "score": score,
            "analysis": analysis,
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


# =========================
# OUTPUT
# =========================

def save_outputs(ranked: List[Dict]):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")

    top_signals = ranked[:TOP_N]

    full_path = os.path.join(OUTPUT_DIR, f"ranked_signals_{timestamp}.json")
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(ranked, f, indent=2)

    top_path = os.path.join(OUTPUT_DIR, f"top_signals_{timestamp}.json")
    with open(top_path, "w", encoding="utf-8") as f:
        json.dump(top_signals, f, indent=2)

    summary = [
        {
            "title": x["title"],
            "url": x.get("url"),
            "signal": x["analysis"].get("primary_signal"),
            "decision": x["analysis"].get("decision"),
            "time_horizon": x["analysis"].get("time_horizon"),
            "confidence": x["analysis"].get("confidence"),
            "score": x["score"],
        }
        for x in top_signals
    ]

    summary_path = os.path.join(OUTPUT_DIR, f"weekly_summary_{timestamp}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("[OK] Saved:")
    print(f" - {full_path}")
    print(f" - {top_path}")
    print(f" - {summary_path}")


# =========================
# MAIN
# =========================

def main():
    print("Loading enriched items...")
    items = load_enriched_items()
    print(f"Loaded: {len(items)} items")

    print("Filtering monitor/shortlist...")
    filtered = filter_signals(items)
    print(f"Filtered: {len(filtered)} signals")

    print("Ranking...")
    ranked = rank_signals(filtered)

    print("Saving outputs...")
    save_outputs(ranked)

    print("Done.")


if __name__ == "__main__":
    main()
    