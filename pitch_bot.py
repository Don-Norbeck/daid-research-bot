import os
import json
from datetime import datetime, UTC
from typing import List, Dict

OUTPUT_DIR = "data/outputs"


# =========================
# LOAD LATEST SUMMARY
# =========================

def latest_weekly_summary_path() -> str:
    candidates = [
        os.path.join(OUTPUT_DIR, f)
        for f in os.listdir(OUTPUT_DIR)
        if f.startswith("weekly_summary_") and f.endswith(".json")
    ]
    if not candidates:
        raise FileNotFoundError("No weekly_summary JSON files found in data/outputs")

    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def load_weekly_summary(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# CLASSIFICATION
# =========================

def classify_theme(signal: Dict) -> str:
    text = (
        f"{signal.get('title', '')} "
        f"{signal.get('signal', '')}"
    ).lower()

    if any(k in text for k in ["agent", "agentic", "retriever", "openclaw", "nanoclaw"]):
        return "agentic_systems"
    if any(k in text for k in ["bio", "genome", "dna", "chemistry", "materials", "drug"]):
        return "scientific_acceleration"
    if any(k in text for k in ["security", "misuse", "exploit", "surveillance", "cyber"]):
        return "misuse_security"
    if any(k in text for k in ["policy", "regulation", "legal", "governance"]):
        return "policy_governance"
    if any(k in text for k in ["nvidia", "microsoft", "google", "deepmind", "docker"]):
        return "power_concentration"

    return "general_capability"


# =========================
# ARTICLE IDEAS
# =========================

def article_idea_from_signal(signal: Dict) -> Dict:
    title = signal.get("title", "")
    summary = signal.get("signal", "")
    url = signal.get("url")
    theme = classify_theme(signal)

    templates = {
        "agentic_systems": {
            "headline": "Agentic open tools are moving faster than governance",
            "angle": f"The signal behind '{title}' is not just product momentum. It is the accelerating spread, adaptation, and normalization of agentic tooling outside mature governance controls.",
            "format": "DAID article"
        },
        "scientific_acceleration": {
            "headline": "AI is quietly accelerating science faster than policy is tracking it",
            "angle": f"'{title}' points to a broader pattern: AI capability gains in biology, chemistry, and materials science may compound into industrial and geopolitical advantage before governance catches up.",
            "format": "DAID article"
        },
        "misuse_security": {
            "headline": "Security framing does not eliminate misuse risk",
            "angle": f"'{title}' suggests that security-wrapped capability expansion can still broaden access, normalize risky tooling, and shift the misuse surface outward.",
            "format": "DAID article"
        },
        "policy_governance": {
            "headline": "The governance signal behind this week’s AI developments",
            "angle": f"'{title}' is less about the announcement itself and more about the policy and accountability gap surrounding real-world deployment.",
            "format": "Policy brief"
        },
        "power_concentration": {
            "headline": "The next AI moat may be infrastructure plus scientific acceleration",
            "angle": f"'{title}' highlights how frontier capability increasingly depends on firms with unique compute, data, and research stack advantages.",
            "format": "DAID article"
        },
        "general_capability": {
            "headline": "Capability progress is not neutral when institutions lag",
            "angle": f"'{title}' is another example of how incremental capability gains can accumulate into meaningful societal and governance pressure over time.",
            "format": "LinkedIn long-form"
        },
    }

    chosen = templates.get(theme, templates["general_capability"])

    return {
        "source_title": title,
        "url": url,
        "theme": theme,
        "headline": chosen["headline"],
        "angle": chosen["angle"],
        "supporting_signal": summary,
        "format": chosen["format"],
    }


# =========================
# LINKEDIN ANGLES
# =========================

def linkedin_angle_from_signal(signal: Dict) -> Dict:
    title = signal.get("title", "")
    summary = signal.get("signal", "")
    url = signal.get("url")

    return {
        "title": title,
        "url": url,
        "hook": f"This week’s signal is not just about '{title}'. It is about what happens when capability moves faster than oversight.",
        "body_seed": f"{summary} The real issue is not whether this is impressive. It is whether institutions, companies, and users are ready for the downstream effects.",
        "cta": "Worth watching now, before this shifts from technical milestone to governance headache."
    }


# =========================
# RISK SCORE DRIVERS
# =========================

def risk_score_driver_from_signal(signal: Dict) -> Dict:
    title = signal.get("title", "")
    url = signal.get("url")
    theme = classify_theme(signal)

    weight_map = {
        "agentic_systems": 4,
        "misuse_security": 5,
        "power_concentration": 3,
        "scientific_acceleration": 3,
        "policy_governance": 4,
        "general_capability": 2,
    }

    rationale_map = {
        "agentic_systems": "Agentic tooling spread increases the chance of broader deployment before guardrails mature.",
        "misuse_security": "Security-labeled capability growth can still increase misuse exposure and operational risk.",
        "power_concentration": "Control over frontier infrastructure and research pipelines can deepen dependency and asymmetry.",
        "scientific_acceleration": "Accelerated bio, chemistry, or materials discovery can create second-order industrial and policy pressure.",
        "policy_governance": "Governance-related developments can quickly alter incentives, accountability, or enforcement expectations.",
        "general_capability": "Incremental capability gains can still contribute to aggregate systemic pressure.",
    }

    return {
        "title": title,
        "url": url,
        "theme": theme,
        "suggested_risk_points": weight_map.get(theme, 2),
        "rationale": rationale_map.get(theme, rationale_map["general_capability"]),
    }


# =========================
# BUILD PACKAGE
# =========================

def build_pitch_package(signals: List[Dict]) -> Dict:
    article_ideas = [article_idea_from_signal(s) for s in signals]
    linkedin_angles = [linkedin_angle_from_signal(s) for s in signals[:5]]
    risk_drivers = [risk_score_driver_from_signal(s) for s in signals]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_count": len(signals),
        "article_ideas": article_ideas,
        "linkedin_angles": linkedin_angles,
        "risk_score_candidates": risk_drivers,
    }


# =========================
# SAVE
# =========================

def save_pitch_package(payload: Dict) -> str:
    filename = f"pitch_ideas_{datetime.now(UTC).strftime('%Y-%m-%d')}.json"
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return path


# =========================
# MAIN
# =========================

def main():
    summary_path = latest_weekly_summary_path()
    signals = load_weekly_summary(summary_path)

    payload = build_pitch_package(signals)
    saved_path = save_pitch_package(payload)

    print(f"[OK] Loaded summary: {summary_path}")
    print(f"[OK] Built pitch package from {len(signals)} signals")
    print(f"[OK] Saved: {saved_path}")


if __name__ == "__main__":
    main()