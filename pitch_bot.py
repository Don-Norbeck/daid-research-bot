"""
pitch_bot.py

Transforms ranked signals into pitch-ready content for DarkAIDefense.

Outputs:
  data/outputs/pitch_report_YYYY-MM-DD.md   → drops directly into Ulysses
  data/outputs/pitch_ideas_YYYY-MM-DD.json  → structured data for the UI
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

OUTPUT_DIR = Path("data/outputs")

GENX_PATTERNS = [
    {
        "keywords": ["job", "jobs", "layoff", "workforce", "employment", "worker", "automat"],
        "pattern": "The Pink Slip Pattern",
        "reference": "dot-com era \"efficiency\" layoffs",
        "frame": "Every tech wave promises net job creation. The net always arrives later. The slips arrive first.",
    },
    {
        "keywords": ["regulate", "regulation", "governance", "policy", "framework", "oversight"],
        "pattern": "The Governance Lag",
        "reference": "Section 230 and social media",
        "frame": "The framework arrives after the product is embedded. It always does. That is not an accident.",
    },
    {
        "keywords": ["agent", "agentic", "autonomous", "multi-agent", "orchestrat"],
        "pattern": "The Wind-Up Toy Problem",
        "reference": "early web crawlers and automated trading bots",
        "frame": "Autonomous systems do not go wrong all at once. They drift. Nobody is watching the drift.",
    },
    {
        "keywords": ["concentration", "monopoly", "dominant", "market share", "platform", "nvidia", "microsoft", "google", "openai"],
        "pattern": "The Platform Lock-In Cycle",
        "reference": "Microsoft's IE bundling and the browser wars",
        "frame": "Infrastructure dependency is not a side effect of winning. It is the strategy.",
    },
    {
        "keywords": ["data", "privacy", "surveillance", "tracking", "personal information"],
        "pattern": "The Data Bargain",
        "reference": "Facebook's 'free' social network",
        "frame": "The product is free. The product is always free. You already know what that means.",
    },
    {
        "keywords": ["misuse", "exploit", "deepfake", "fraud", "scam", "disinformation", "weapon"],
        "pattern": "The Dual-Use Default",
        "reference": "early internet anonymity and the rise of spam",
        "frame": "Every capability that can be misused will be misused. The question is how fast and by whom.",
    },
    {
        "keywords": ["startup", "funding", "valuation", "billion", "unicorn", "invest"],
        "pattern": "The Balloon Animal Economy",
        "reference": "Pets.com and the dot-com bubble",
        "frame": "The valuation is the story until it isn't. Gen X has seen this movie. We know the third act.",
    },
    {
        "keywords": ["productivity", "efficiency", "performative", "meeting", "workflow", "tps"],
        "pattern": "The TPS Report Problem",
        "reference": "Office Space and the theater of corporate productivity",
        "frame": "We automated the reports. We did not automate the meetings about the reports.",
    },
    {
        "keywords": ["bio", "genome", "dna", "drug", "chemistry", "protein", "health", "medical"],
        "pattern": "The Science Acceleration Gap",
        "reference": "the gap between gene sequencing capability and bioethics frameworks",
        "frame": "The science runs faster than the ethics board can schedule a meeting.",
    },
    {
        "keywords": ["content", "media", "creative", "writer", "artist", "copyright", "image gen"],
        "pattern": "The Creative Class Squeeze",
        "reference": "Napster and the music industry's decade of denial",
        "frame": "The industry said it would find a new model. Some did. Most didn't. Ask a musician.",
    },
]

THEME_KEYWORDS = {
    "agentic_systems":           ["agent", "agentic", "multi-agent", "orchestration", "autonomous", "tool use"],
    "labor_disruption":          ["job", "workforce", "employment", "layoff", "automation", "worker", "labor", "profession"],
    "power_concentration":       ["nvidia", "microsoft", "google", "openai", "anthropic", "deepmind", "monopoly", "dominant", "market share"],
    "misuse_security":           ["misuse", "exploit", "surveillance", "weapon", "cyber", "deepfake", "disinformation", "fraud"],
    "governance_policy":         ["policy", "regulation", "law", "governance", "compliance", "legislation", "executive order"],
    "scientific_acceleration":   ["bio", "genome", "dna", "chemistry", "materials", "drug", "protein"],
    "infrastructure_dependency": ["gpu", "compute", "datacenter", "cloud", "inference", "energy", "power grid"],
    "capability_leap":           ["reasoning model", "frontier", "benchmark", "superhuman", "agi", "emergent"],
}


def match_genx_pattern(signal: Dict) -> Optional[Dict]:
    blob = " ".join([
        signal.get("title", ""),
        signal.get("signal", ""),
        signal.get("primary_signal", ""),
        signal.get("darkaidefense_angle", ""),
        signal.get("why_it_matters", ""),
    ]).lower()

    for pattern in GENX_PATTERNS:
        if any(k in blob for k in pattern["keywords"]):
            return pattern

    return None


def classify_theme(signal: Dict) -> str:
    blob = " ".join([
        signal.get("title", ""),
        signal.get("signal", ""),
        signal.get("primary_signal", ""),
    ]).lower()

    for theme, keywords in THEME_KEYWORDS.items():
        if any(k in blob for k in keywords):
            return theme

    return "general_capability"


def load_latest_summary() -> tuple[List[Dict], str]:
    candidates = sorted(
        OUTPUT_DIR.glob("weekly_summary_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("No weekly_summary_*.json found in data/outputs/")

    path = candidates[0]
    data = json.loads(path.read_text(encoding="utf-8"))
    return data, str(path)


def build_article_pitch(signal: Dict) -> Dict:
    theme = classify_theme(signal)
    pattern = match_genx_pattern(signal)
    hook = signal.get("controversy_hook", "").strip()

    return {
        "title": signal.get("title", "Untitled"),
        "url": signal.get("url", ""),
        "theme": theme,
        "decision": signal.get("decision", "monitor"),
        "score": signal.get("score", 0),
        "time_horizon": signal.get("time_horizon", ""),
        "confidence": signal.get("confidence", 0),
        "primary_signal": signal.get("signal") or signal.get("primary_signal", ""),
        "daid_angle": signal.get("darkaidefense_angle", ""),
        "why_it_matters": signal.get("why_it_matters", ""),
        "controversy_hook": hook,
        "genx_pattern": pattern,
    }


def build_linkedin_pitch(signal: Dict) -> Dict:
    pattern = match_genx_pattern(signal)
    title = signal.get("title", "")

    return {
        "title": title,
        "url": signal.get("url", ""),
        "hook": pattern["frame"] if pattern else f"This week's signal is not just about '{title}'. It is about what happens when capability moves faster than oversight.",
        "body_seed": signal.get("signal") or signal.get("primary_signal", ""),
        "cta": "Worth watching now, before this shifts from technical milestone to governance headache.",
        "genx_reference": pattern["reference"] if pattern else None,
    }


def build_risk_driver(signal: Dict) -> Dict:
    theme = classify_theme(signal)

    weight_map = {
        "agentic_systems": 4, "misuse_security": 5, "power_concentration": 3,
        "scientific_acceleration": 3, "governance_policy": 4, "labor_disruption": 4,
        "infrastructure_dependency": 3, "capability_leap": 4, "general_capability": 2,
    }

    rationale_map = {
        "agentic_systems":           "Agentic tooling spread increases deployment before guardrails mature.",
        "misuse_security":           "Security-labeled capability growth still broadens misuse surface.",
        "power_concentration":       "Control over frontier infrastructure deepens dependency and asymmetry.",
        "scientific_acceleration":   "Accelerated discovery creates second-order industrial and policy pressure.",
        "governance_policy":         "Governance developments alter accountability and enforcement expectations.",
        "labor_disruption":          "Displacement signals compound over time even when framed as transformation.",
        "infrastructure_dependency": "Single-vendor or single-platform dependencies create systemic fragility.",
        "capability_leap":           "Non-incremental capability gains can outpace institutional readiness.",
        "general_capability":        "Incremental gains can still contribute to aggregate systemic pressure.",
    }

    return {
        "title": signal.get("title", ""),
        "url": signal.get("url", ""),
        "theme": theme,
        "suggested_risk_points": weight_map.get(theme, 2),
        "rationale": rationale_map.get(theme, rationale_map["general_capability"]),
    }


def format_signal_block(pitch: Dict, index: int) -> str:
    lines = []

    lines.append(f"### {index}. {pitch['title']}")
    lines.append(f"")
    lines.append(f"**Signal class:** {pitch['decision'].upper()} · **Score:** {pitch['score']:.4f} · **Horizon:** {pitch.get('time_horizon', '')} · **Confidence:** {pitch.get('confidence', 0)}")
    lines.append(f"")

    if pitch.get("controversy_hook"):
        lines.append(f"> {pitch['controversy_hook']}")
        lines.append(f"")

    lines.append(f"**Signal:** {pitch['primary_signal']}")
    lines.append(f"")
    lines.append(f"**DAID angle:** {pitch['daid_angle']}")
    lines.append(f"")
    lines.append(f"**Why it matters:** {pitch['why_it_matters']}")
    lines.append(f"")

    pattern = pitch.get("genx_pattern")
    if pattern:
        lines.append(f"**Gen X lens — {pattern['pattern']}**")
        lines.append(f"_Echoes: {pattern['reference']}_")
        lines.append(f"{pattern['frame']}")
        lines.append(f"")

    if pitch.get("url"):
        lines.append(f"**Source:** [{pitch['title']}]({pitch['url']})")
        lines.append(f"")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def build_markdown_report(pitches, trending_block, week_label, source_path):
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    shortlisted = [p for p in pitches if p["decision"] == "shortlist"]
    monitored = [p for p in pitches if p["decision"] == "monitor"]

    lines = [
        f"# DAID Signal Intelligence — {now_str}",
        f"",
        f"_Week: {week_label} · Source: {source_path}_",
        f"",
        f"**{len(shortlisted)} shortlisted · {len(monitored)} monitored · {len(pitches)} total signals**",
        f"",
        f"## Trending Topics",
        f"",
        trending_block,
        f"",
    ]

    if shortlisted:
        lines += [
            f"## Shortlisted Signals",
            f"_These are the strongest pitch candidates this week._",
            f"",
        ]
        for i, pitch in enumerate(shortlisted, start=1):
            lines.append(format_signal_block(pitch, i))

    if monitored:
        lines += [
            f"## Monitor Signals",
            f"_Worth watching. Not ready to pitch yet._",
            f"",
        ]
        for pitch in monitored:
            hook = pitch.get("controversy_hook", "")
            hook_str = f" — _{hook}_" if hook else ""
            lines.append(f"- **{pitch['title']}**{hook_str}")
            lines.append(f"  {pitch['primary_signal']}")
            if pitch.get("url"):
                lines.append(f"  [{pitch['url']}]({pitch['url']})")
            lines.append(f"")

    return "\n".join(lines)


def save_outputs(pitches, linkedin, risk_drivers, markdown_report):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    md_path = OUTPUT_DIR / f"pitch_report_{timestamp}.md"
    md_path.write_text(markdown_report, encoding="utf-8")

    json_path = OUTPUT_DIR / f"pitch_ideas_{timestamp}.json"
    json_path.write_text(
        json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_count": len(pitches),
            "article_ideas": pitches,
            "linkedin_angles": linkedin,
            "risk_score_candidates": risk_drivers,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return str(md_path), str(json_path)


def main():
    from trending_tracker import record_week, format_trending_block, get_week_label

    print("Loading weekly summary...")
    signals, source_path = load_latest_summary()
    print(f"Loaded {len(signals)} signals from {source_path}")

    print("Recording trends...")
    week_entry = record_week(signals)
    print(f"Week: {week_entry['week']} — themes: {week_entry['themes']}")

    print("Building pitches...")
    pitches = [build_article_pitch(s) for s in signals]
    linkedin = [build_linkedin_pitch(s) for s in signals[:5]]
    risk_drivers = [build_risk_driver(s) for s in signals]

    pitches.sort(key=lambda p: (0 if p["decision"] == "shortlist" else 1, -p.get("score", 0)))

    trending_block = format_trending_block(lookback_weeks=4)

    print("Building Markdown report...")
    markdown_report = build_markdown_report(
        pitches=pitches,
        trending_block=trending_block,
        week_label=get_week_label(),
        source_path=source_path,
    )

    md_path, json_path = save_outputs(pitches, linkedin, risk_drivers, markdown_report)

    print(f"[OK] Markdown report: {md_path}")
    print(f"[OK] JSON output:     {json_path}")

    shortlisted = [p for p in pitches if p["decision"] == "shortlist"]
    if shortlisted:
        top = shortlisted[0]
        print(f"\nTop signal this week:")
        print(f"  {top['title']}")
        if top.get("controversy_hook"):
            print(f"  Hook: {top['controversy_hook']}")
        pattern = top.get("genx_pattern")
        if pattern:
            print(f"  Gen X lens: {pattern['pattern']}")


if __name__ == "__main__":
    main()