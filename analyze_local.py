import argparse
import json
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

DATA_DIR = Path("data")
ITEMS_DIR = DATA_DIR / "items"
ENRICHED_DIR = DATA_DIR / "enriched"
PROMPTS_DIR = Path("prompts")
PROMPT_FILE = PROMPTS_DIR / "analyze_article.txt"
LOGS_DIR = Path("logs")
LOG_FILE = LOGS_DIR / "analyze_local.jsonl"

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
LOCAL_MODEL = "mistral-nemo:12b"

REQUEST_TIMEOUT = 180
MAX_RAW_TEXT_CHARS = 12000
SLEEP_BETWEEN_CALLS_SEC = 0.25
ONLY_UNANALYZED = True

# Raised from 50. For normal weekly runs this is plenty.
# Use --days-back 30 --max 200 for a backlog clear.
DEFAULT_MAX_PER_RUN = 100


def ensure_dirs() -> None:
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log_event(event: Dict[str, Any]) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8").strip()


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log_event({
            "module": "load_json_file",
            "status": "error",
            "path": str(path),
            "error": str(e),
        })
        return None


def save_json_file(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_published_at(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def build_article_input(item: Dict[str, Any]) -> str:
    raw_text = item.get("raw_text", "") or ""
    raw_text = normalize_whitespace(raw_text)[:MAX_RAW_TEXT_CHARS]

    article_payload = {
        "title": item.get("title"),
        "source_feed": item.get("source_feed"),
        "url": item.get("url"),
        "published_at": item.get("published_at"),
        "summary": item.get("summary"),
        "raw_text": raw_text,
    }

    return json.dumps(article_payload, ensure_ascii=False, indent=2)


def coerce_analysis_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    allowed_decisions = {"ignore", "monitor", "shortlist"}
    allowed_time_horizon = {"immediate", "near_term", "long_term", "archival"}

    def clamp_float(value: Any) -> float:
        try:
            x = float(value)
        except Exception:
            x = 0.0
        return max(0.0, min(1.0, x))

    decision = str(data.get("decision", "ignore")).strip().lower()
    if decision not in allowed_decisions:
        decision = "ignore"

    time_horizon = str(data.get("time_horizon", "archival")).strip().lower()
    if time_horizon not in allowed_time_horizon:
        time_horizon = "archival"

    primary_signal = str(data.get("primary_signal", "")).strip()
    darkaidefense_angle = str(data.get("darkaidefense_angle", "")).strip()
    why_it_matters = str(data.get("why_it_matters", "")).strip()
    confidence = clamp_float(data.get("confidence", 0.0))

    # controversy_hook: optional field added in updated prompt.
    # Older enriched files will not have it — default to empty string.
    controversy_hook = str(data.get("controversy_hook", "")).strip()

    return {
        "decision": decision,
        "time_horizon": time_horizon,
        "primary_signal": primary_signal,
        "darkaidefense_angle": darkaidefense_angle,
        "why_it_matters": why_it_matters,
        "confidence": confidence,
        "controversy_hook": controversy_hook,
    }


def build_full_prompt(prompt_text: str, article_text: str) -> str:
    return f"{prompt_text}\n\nArticle to analyze:\n{article_text}"


def check_ollama_available() -> None:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(
            f"Ollama is not reachable at {OLLAMA_TAGS_URL}. Error: {e}"
        )


def ensure_model_loaded() -> None:
    print(f"Ensuring model is loaded: {LOCAL_MODEL}")

    payload = {
        "model": LOCAL_MODEL,
        "prompt": "Ready.",
        "stream": False,
        "options": {
            "num_predict": 1,
            "temperature": 0.0,
        },
    }

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        print("Model ready.")
    except Exception as e:
        raise RuntimeError(f"Failed to load model {LOCAL_MODEL}: {e}")


def call_local_model(prompt_text: str, article_text: str) -> Dict[str, Any]:
    full_prompt = build_full_prompt(prompt_text=prompt_text, article_text=article_text)

    schema = {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["ignore", "monitor", "shortlist"]
            },
            "time_horizon": {
                "type": "string",
                "enum": ["immediate", "near_term", "long_term", "archival"]
            },
            "primary_signal": {"type": "string"},
            "darkaidefense_angle": {"type": "string"},
            "why_it_matters": {"type": "string"},
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "controversy_hook": {"type": "string"},
        },
        "required": [
            "decision",
            "time_horizon",
            "primary_signal",
            "darkaidefense_angle",
            "why_it_matters",
            "confidence",
            "controversy_hook",
        ]
    }

    payload = {
        "model": LOCAL_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "format": schema,
        "options": {
            "temperature": 0.0,
        },
    }

    response = requests.post(
        OLLAMA_API_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    body = response.json()
    content = body.get("response", "").strip()

    try:
        parsed = json.loads(content)
    except Exception as e:
        raise ValueError(
            f"Model returned non-JSON structured output. Raw content: {content[:1000]} | Error: {e}"
        )

    return coerce_analysis_schema(parsed)


def enriched_path_for_item(item_path: Path) -> Path:
    return ENRICHED_DIR / item_path.name


def item_already_analyzed(item_path: Path) -> bool:
    return enriched_path_for_item(item_path).exists()


def analyze_item(item_path: Path, prompt_text: str) -> bool:
    item = load_json_file(item_path)
    if item is None:
        return False

    doc_id = item.get("doc_id", item_path.stem)
    article_text = build_article_input(item)
    output_path = enriched_path_for_item(item_path)

    last_error = None
    analysis: Optional[Dict[str, Any]] = None

    for attempt in range(2):
        try:
            analysis = call_local_model(prompt_text=prompt_text, article_text=article_text)
            break
        except Exception as e:
            last_error = e
            if attempt == 0:
                time.sleep(1.0)
            else:
                log_event({
                    "module": "analyze_item",
                    "status": "error",
                    "doc_id": doc_id,
                    "input_path": str(item_path),
                    "output_path": str(output_path),
                    "error": str(last_error),
                })
                return False

    if analysis is None:
        log_event({
            "module": "analyze_item",
            "status": "error",
            "doc_id": doc_id,
            "input_path": str(item_path),
            "output_path": str(output_path),
            "error": "Analysis was None after retries",
        })
        return False

    enriched_payload = {
        "doc_id": doc_id,
        "source_item_path": str(item_path),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "title": item.get("title"),
        "url": item.get("url"),
        "source_feed": item.get("source_feed"),
        "published_at": item.get("published_at"),
        "summary": item.get("summary"),
        "analysis": analysis,
        "status": "analyzed",
    }

    save_json_file(output_path, enriched_payload)

    log_event({
        "module": "analyze_item",
        "status": "saved",
        "doc_id": doc_id,
        "input_path": str(item_path),
        "output_path": str(output_path),
        "decision": analysis.get("decision"),
        "time_horizon": analysis.get("time_horizon"),
        "confidence": analysis.get("confidence"),
        "controversy_hook_present": bool(analysis.get("controversy_hook")),
    })
    return True


def list_candidate_items(days_back: Optional[int], max_items: int) -> List[Path]:
    """
    Return candidate items sorted newest-first.

    days_back: if set, only include items published within this window.
               Items with no parseable published_at are always included.
    max_items: hard cap on returned candidates.
    """
    cutoff: Optional[datetime] = None
    if days_back is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    candidates: List[tuple[Path, datetime]] = []

    for item_path in ITEMS_DIR.glob("*.json"):
        if ONLY_UNANALYZED and item_already_analyzed(item_path):
            continue

        item = load_json_file(item_path)
        if item is None:
            continue

        published_dt = parse_published_at(item.get("published_at"))

        # Apply date filter if set
        if cutoff is not None and published_dt is not None:
            if published_dt < cutoff:
                continue

        if published_dt is None:
            published_dt = datetime.min.replace(tzinfo=timezone.utc)

        candidates.append((item_path, published_dt))

    candidates.sort(key=lambda x: x[1], reverse=True)

    return [path for path, _ in candidates[:max_items]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze captured RSS items with local LLM."
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=None,
        help="Only analyze items published within this many days. "
             "Default: no date filter (analyze all unanalyzed items up to --max). "
             "Use --days-back 30 for a targeted backlog clear.",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=DEFAULT_MAX_PER_RUN,
        help=f"Maximum items to analyze in this run (default: {DEFAULT_MAX_PER_RUN}). "
             "Set higher for backlog clearing.",
    )
    parser.add_argument(
        "--reanalyze",
        action="store_true",
        default=False,
        help="Re-analyze items that already have an enriched file. "
             "Use after updating the prompt to pick up controversy_hook.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    global ONLY_UNANALYZED
    if args.reanalyze:
        ONLY_UNANALYZED = False
        print("[INFO] --reanalyze: will overwrite existing enriched files")

    ensure_dirs()
    prompt_text = load_prompt()

    check_ollama_available()
    ensure_model_loaded()

    candidates = list_candidate_items(days_back=args.days_back, max_items=args.max)

    print(f"Using model: {LOCAL_MODEL}")
    print(f"Ollama endpoint: {OLLAMA_API_URL}")
    print(f"Days-back filter: {args.days_back if args.days_back else 'none'}")
    print(f"Max per run: {args.max}")
    print(f"Candidate items: {len(candidates)}")

    if not candidates:
        print("No items to analyze.")
        return

    saved_count = 0
    error_count = 0

    for idx, item_path in enumerate(candidates, start=1):
        print(f"[{idx}/{len(candidates)}] Analyzing: {item_path.name}")
        ok = analyze_item(item_path=item_path, prompt_text=prompt_text)
        if ok:
            saved_count += 1
        else:
            error_count += 1
        time.sleep(SLEEP_BETWEEN_CALLS_SEC)

    print("Done.")
    print(f"Saved analyses: {saved_count}")
    print(f"Errors: {error_count}")


if __name__ == "__main__":
    main()