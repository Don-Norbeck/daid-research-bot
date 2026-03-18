import os
import json
from datetime import datetime, timedelta, timezone
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
# DEDUPLICATION
# Fix: same article captured on different days produces multiple enriched
# files with different doc_ids. Deduplicate by URL, keeping the most
# recently analyzed copy.
# =========================

def deduplicate_by_url(items: List[Dict]) -> List[Dict]:
    seen: Dict[str, Dict] = {}

    for item in items:
        url = item.get("url", "").strip()
        if not url:
            # No URL — keep as-is, use doc_id as key
            key = item.get("doc_id", id(item))
            seen[key] = item
            continue

        existing = seen.get(url)
        if existing is None:
            seen[url] = item
        else:
            # Keep whichever was analyzed more recently
            existing_ts = existing.get("analyzed_at", "")
            current_ts = item.get("analyzed_at", "")
            if current_ts > existing_ts:
                seen[url] = item

    deduped = list(seen.values())
    removed = len(items) - len(deduped)
    if removed > 0:
        print(f"[INFO] Deduplicated {removed} duplicate URL(s)")

    return deduped


# =========================
# DATE FILTER (WEEKLY WINDOW)
# Fix: datetime.utcnow() returns a naive datetime; enriched items store
# timezone-aware ISO strings. Mixed comparison raises TypeError, which
# was silently caught and returned True (items passed through incorrectly).
# Now using timezone.utc throughout.
# =========================

def parse_dt_utc(value: str) -> datetime:
    """
    Parse an ISO 8601 or RFC 2822 datetime string and return a
    timezone-aware UTC datetime. Raises ValueError if unparseable.
    """
    # Handle Z suffix
    cleaned = value.strip().replace("Z", "+00:00")

    # Try ISO format first
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    # Try RFC 2822 (e.g. "Mon, 01 Jan 2024 00:00:00 GMT")
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(value.strip())
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # Try bare date
    try:
        dt = datetime.strptime(value.strip()[:10], "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    raise ValueError(f"Unparseable datetime: {value!r}")


def is_within_window(item: Dict) -> bool:
    published = item.get("published_at")
    if not published:
        return True

    try:
        dt = parse_dt_utc(published)
        cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
        return dt >= cutoff
    except Exception:
        # If we genuinely cannot parse the date, include the item
        # rather than silently drop it, but log a warning
        print(f"[WARN] Could not parse published_at for doc_id={item.get('doc_id')}: {published!r} — included by default")
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
# Fix: datetime.utcnow() replaced with timezone-aware equivalent
# =========================

def save_outputs(ranked: List[Dict]):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

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
            "darkaidefense_angle": x["analysis"].get("darkaidefense_angle", ""),
            "why_it_matters": x["analysis"].get("why_it_matters", ""),
            "controversy_hook": x["analysis"].get("controversy_hook", ""),
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

    print("Deduplicating by URL...")
    items = deduplicate_by_url(items)
    print(f"After dedup: {len(items)} items")

    print("Filtering monitor/shortlist within weekly window...")
    filtered = filter_signals(items)
    print(f"Filtered: {len(filtered)} signals")

    print("Ranking...")
    ranked = rank_signals(filtered)

    print("Saving outputs...")
    save_outputs(ranked)

    print("Done.")


if __name__ == "__main__":
    main()