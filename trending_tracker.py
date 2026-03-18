"""
trending_tracker.py

Tracks topic and theme frequency across weekly pipeline runs.
Persists to data/trends.json so you can see what is building
vs. spiking vs. fading over time.

Called automatically by pitch_bot.py. Can also be run standalone.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

TRENDS_FILE = Path("data/trends.json")
OUTPUT_DIR = Path("data/outputs")

# Keyword clusters mapped to human-readable theme labels.
# Order matters: first match wins.
THEME_CLUSTERS = {
    "agentic_systems":          ["agent", "agentic", "multi-agent", "orchestration", "autonomous", "tool use", "function calling"],
    "labor_disruption":         ["job", "jobs", "workforce", "employment", "layoff", "automation", "worker", "labor", "profession", "white-collar", "knowledge worker"],
    "power_concentration":      ["nvidia", "microsoft", "google", "openai", "anthropic", "deepmind", "meta ai", "amazon", "monopoly", "dominant", "market share", "infrastructure control"],
    "misuse_security":          ["misuse", "exploit", "surveillance", "weapon", "cyber", "deepfake", "disinformation", "fraud", "scam", "manipulation"],
    "governance_policy":        ["policy", "regulation", "law", "governance", "compliance", "legislation", "congress", "eu ai act", "executive order", "accountability"],
    "scientific_acceleration":  ["bio", "genome", "dna", "chemistry", "materials", "drug discovery", "protein", "climate model", "physics"],
    "infrastructure_dependency": ["gpu", "compute", "datacenter", "cloud dependency", "inference", "energy", "power grid", "supply chain"],
    "capability_leap":          ["gpt-5", "reasoning model", "frontier model", "benchmark", "superhuman", "agi", "general intelligence", "emergent"],
}


def load_trends() -> Dict[str, Any]:
    if not TRENDS_FILE.exists():
        return {"weeks": [], "lifetime": {}}
    try:
        return json.loads(TRENDS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"weeks": [], "lifetime": {}}


def save_trends(data: Dict[str, Any]) -> None:
    TRENDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRENDS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def classify_theme(text: str) -> str:
    lower = text.lower()
    for theme, keywords in THEME_CLUSTERS.items():
        if any(k in lower for k in keywords):
            return theme
    return "general_capability"


def score_items_to_themes(signals: List[Dict]) -> Dict[str, int]:
    """
    Count theme frequency across a list of ranked/summary signals.
    Each signal is scored by its primary_signal + title + darkaidefense_angle text.
    """
    counts: Dict[str, int] = {theme: 0 for theme in THEME_CLUSTERS}
    counts["general_capability"] = 0

    for item in signals:
        blob = " ".join([
            item.get("title", ""),
            item.get("signal", ""),
            item.get("primary_signal", ""),
            item.get("darkaidefense_angle", ""),
        ])
        theme = classify_theme(blob)
        counts[theme] = counts.get(theme, 0) + 1

    # Drop zero-count themes to keep output clean
    return {k: v for k, v in counts.items() if v > 0}


def get_week_label() -> str:
    now = datetime.now(timezone.utc)
    # ISO week: e.g. "2026-W11"
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def record_week(signals: List[Dict]) -> Dict[str, Any]:
    """
    Record this week's theme counts into trends.json.
    Returns the week entry so pitch_bot can use it directly.
    """
    trends = load_trends()
    week_label = get_week_label()

    theme_counts = score_items_to_themes(signals)
    total_signals = len(signals)

    week_entry = {
        "week": week_label,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "total_signals": total_signals,
        "themes": theme_counts,
    }

    # Replace existing entry for this week if re-running
    trends["weeks"] = [w for w in trends["weeks"] if w.get("week") != week_label]
    trends["weeks"].append(week_entry)

    # Keep only last 12 weeks
    trends["weeks"].sort(key=lambda w: w.get("week", ""), reverse=True)
    trends["weeks"] = trends["weeks"][:12]

    # Update lifetime counts
    lifetime = trends.get("lifetime", {})
    for theme, count in theme_counts.items():
        lifetime[theme] = lifetime.get(theme, 0) + count
    trends["lifetime"] = lifetime

    save_trends(trends)
    return week_entry


def get_trending_summary(lookback_weeks: int = 4) -> List[Dict[str, Any]]:
    """
    Returns themes ranked by recent frequency over the last N weeks,
    with a trend direction: rising / stable / fading.
    """
    trends = load_trends()
    weeks = trends.get("weeks", [])

    if not weeks:
        return []

    recent = weeks[:lookback_weeks]
    prior = weeks[lookback_weeks:lookback_weeks * 2]

    # Sum counts per theme across recent and prior windows
    recent_totals: Dict[str, int] = {}
    for w in recent:
        for theme, count in w.get("themes", {}).items():
            recent_totals[theme] = recent_totals.get(theme, 0) + count

    prior_totals: Dict[str, int] = {}
    for w in prior:
        for theme, count in w.get("themes", {}).items():
            prior_totals[theme] = prior_totals.get(theme, 0) + count

    result = []
    for theme, recent_count in sorted(recent_totals.items(), key=lambda x: x[1], reverse=True):
        prior_count = prior_totals.get(theme, 0)

        if prior_count == 0:
            direction = "new" if recent_count > 0 else "stable"
        elif recent_count > prior_count * 1.25:
            direction = "rising"
        elif recent_count < prior_count * 0.75:
            direction = "fading"
        else:
            direction = "stable"

        result.append({
            "theme": theme,
            "recent_count": recent_count,
            "prior_count": prior_count,
            "trend": direction,
        })

    return result


def format_trending_block(lookback_weeks: int = 4) -> str:
    """
    Returns a Markdown block summarizing trending topics.
    Used by pitch_bot to inject into the weekly report.
    """
    summary = get_trending_summary(lookback_weeks)
    if not summary:
        return "_No trend data yet. Will build after the first few weekly runs._\n"

    lines = [f"_Based on last {lookback_weeks} weeks of signals_\n"]
    lines.append("| Theme | Recent | Trend |")
    lines.append("|---|---|---|")

    trend_emoji = {
        "rising": "↑ Rising",
        "fading": "↓ Fading",
        "stable": "→ Stable",
        "new":    "★ New",
    }

    for item in summary:
        label = item["theme"].replace("_", " ").title()
        trend = trend_emoji.get(item["trend"], item["trend"])
        lines.append(f"| {label} | {item['recent_count']} signals | {trend} |")

    return "\n".join(lines)


if __name__ == "__main__":
    # Standalone: load latest weekly summary and record it
    import sys

    candidates = sorted(
        [f for f in OUTPUT_DIR.glob("weekly_summary_*.json")],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not candidates:
        print("[WARN] No weekly_summary_*.json found in data/outputs/")
        sys.exit(1)

    latest = candidates[0]
    signals = json.loads(latest.read_text(encoding="utf-8"))

    week_entry = record_week(signals)
    print(f"[OK] Recorded week: {week_entry['week']}")
    print(f"     Signals: {week_entry['total_signals']}")
    print(f"     Themes: {week_entry['themes']}")

    print("\nTrending (last 4 weeks):")
    for item in get_trending_summary():
        print(f"  {item['theme']:30s} {item['recent_count']:3d} signals  [{item['trend']}]")