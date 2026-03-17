import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

DATA_DIR = Path("data")
ITEMS_DIR = DATA_DIR / "items"
LOGS_DIR = Path("logs")
LOG_FILE = LOGS_DIR / "watchdog.jsonl"
FEEDS_FILE = Path("feeds.json")
STATE_FILE = DATA_DIR / "state.json"

HTTP_TIMEOUT = 30
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
ROBOTS_UA = "DAIDWatchdog"

TOPIC_KEYWORDS = {
    "policy": ["policy", "regulation", "law", "governance", "compliance"],
    "agents": ["agent", "agentic", "multi-agent", "orchestration"],
    "safety": ["safety", "alignment", "misuse", "harm", "security"],
    "labor": ["jobs", "workforce", "employment", "automation", "labor"],
    "infrastructure": ["gpu", "inference", "model serving", "compute", "datacenter"],
}


def ensure_dirs() -> None:
    ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log_event(event: Dict[str, Any]) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_feeds() -> List[str]:
    if not FEEDS_FILE.exists():
        return []
    try:
        return json.loads(FEEDS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log_event({
            "module": "config",
            "status": "error",
            "file": str(FEEDS_FILE),
            "error": str(e),
        })
        return []


def load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {
            "last_run_started_at": None,
            "last_run_completed_at": None,
        }

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log_event({
            "module": "state",
            "status": "error",
            "file": str(STATE_FILE),
            "error": str(e),
        })
        return {
            "last_run_started_at": None,
            "last_run_completed_at": None,
        }


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def parse_feed_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    value = value.strip()

    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            return dt.astimezone(timezone.utc)
    except Exception:
        pass

    try:
        cleaned = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    try:
        dt = datetime.fromisoformat(value[:10])
        dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def load_existing_url_hashes() -> set[str]:
    hashes = set()
    for path in ITEMS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            url_hash = data.get("url_hash")
            if url_hash:
                hashes.add(url_hash)
        except Exception:
            continue
    return hashes


def stable_doc_id(url: str) -> str:
    digest = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:16]
    return f"{datetime.now(timezone.utc).date().isoformat()}-{digest}"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def allowed_by_robots(url: str) -> bool:
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(ROBOTS_UA, url)
    except Exception:
        return True


def extract_meta_description(html: str) -> Optional[str]:
    patterns = [
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, flags=re.IGNORECASE)
        if m:
            return normalize_whitespace(m.group(1))
    return None


def extract_publish_date(html: str) -> Optional[str]:
    candidates = []
    patterns = [
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+itemprop=["\']datePublished["\'][^>]+content=["\']([^"\']+)["\']',
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'"dateModified"\s*:\s*"([^"]+)"',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, html, flags=re.IGNORECASE):
            candidates.append(m.group(1).strip())

    if not candidates:
        return None

    raw = candidates[0]
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", raw)
    return match.group(1) if match else None


def guess_type_from_url(url: str) -> str:
    u = url.lower()
    if any(host in u for host in ["youtube.com", "youtu.be", "vimeo.com"]):
        return "video"
    if any(host in u for host in ["x.com", "twitter.com", "reddit.com", "linkedin.com/posts/"]):
        return "post"
    return "article"


def simple_topic_match(title: str, text: str) -> List[str]:
    blob = f"{title} {text}".lower()
    matched = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword.lower() in blob for keyword in keywords):
            matched.append(topic)
    return matched


def simple_summary(text: str, max_chars: int = 500) -> str:
    if not text:
        return ""
    return normalize_whitespace(text)[:max_chars]


def parse_rss_feed(feed_url: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    try:
        response = requests.get(
            feed_url,
            headers={"User-Agent": UA},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()

        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "published_hint": pub_date,
                    "source_feed": feed_url,
                })

        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns):
                title = entry.findtext("atom:title", default="", namespaces=ns).strip()
                link_el = entry.find("atom:link", ns)
                link = link_el.attrib.get("href", "").strip() if link_el is not None else ""
                pub_date = entry.findtext("atom:published", default="", namespaces=ns).strip()
                if title and link:
                    items.append({
                        "title": title,
                        "link": link,
                        "published_hint": pub_date,
                        "source_feed": feed_url,
                    })
    except Exception as e:
        log_event({
            "module": "rss",
            "status": "error",
            "feed_url": feed_url,
            "error": str(e),
        })

    return items


def fetch_page_text_and_date(url: str) -> Tuple[str, Optional[str]]:
    allow = allowed_by_robots(url)
    try:
        response = requests.get(url, headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
    except Exception as e:
        log_event({
            "module": "fetch",
            "status": "error",
            "url": url,
            "error": str(e),
        })
        return "", None

    if response.status_code != 200 or not response.text:
        log_event({
            "module": "fetch",
            "status": "bad_response",
            "url": url,
            "status_code": response.status_code,
        })
        return "", None

    html = response.text

    if not allow:
        page_text = extract_meta_description(html) or ""
    else:
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = normalize_whitespace(text)
        page_text = text[:10000]
        if len(page_text) < 200:
            page_text = extract_meta_description(html) or page_text

    published_iso = extract_publish_date(html)
    return page_text, published_iso


def save_item(item: Dict[str, Any]) -> Path:
    path = ITEMS_DIR / f"{item['doc_id']}.json"
    path.write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def process_candidate(
    title: str,
    link: str,
    source_feed: Optional[str],
    published_hint: Optional[str],
    existing_url_hashes: set[str],
    last_run_completed_at: Optional[datetime],
) -> None:
    if not title or not link:
        return

    feed_dt = parse_feed_datetime(published_hint)
    if last_run_completed_at and feed_dt and feed_dt <= last_run_completed_at:
        log_event({
            "module": "pipeline",
            "status": "skipped_old",
            "url": link,
            "published_hint": published_hint,
        })
        return

    url_hash = hashlib.sha256(link.strip().encode("utf-8")).hexdigest()

    if url_hash in existing_url_hashes:
        log_event({
            "module": "pipeline",
            "status": "skipped_duplicate",
            "url": link,
        })
        return

    page_text, published_date = fetch_page_text_and_date(link)

    topics: List[str] = []

    item = {
        "doc_id": stable_doc_id(link),
        "title": title,
        "url": link,
        "url_hash": url_hash,
        "source_feed": source_feed,
        "content_type": guess_type_from_url(link),
        "published_at": published_date or published_hint,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "raw_text": page_text,
        "summary": simple_summary(page_text),
        "topics": topics,
        "status": "captured",
    }

    saved_path = save_item(item)
    existing_url_hashes.add(url_hash)

    log_event({
        "module": "pipeline",
        "status": "saved",
        "doc_id": item["doc_id"],
        "url": item["url"],
        "path": str(saved_path),
        "topics": topics,
    })


def main() -> None:
    ensure_dirs()
    feeds = load_feeds()
    state = load_state()
    seen_links = set()
    existing_url_hashes = load_existing_url_hashes()

    now_utc = datetime.now(timezone.utc)

    state["last_run_started_at"] = now_utc.isoformat()
    save_state(state)

    last_run_completed_at = parse_feed_datetime(state.get("last_run_completed_at"))

    print(f"Loaded {len(existing_url_hashes)} existing URL hashes")
    print(f"Last successful run: {state.get('last_run_completed_at')}")

    if not feeds:
        print("No feeds found in feeds.json")
        return

    print(f"Loaded {len(feeds)} feeds")

    for feed in feeds:
        print(f"Checking feed: {feed}")
        for entry in parse_rss_feed(feed):
            link = entry["link"]
            if link in seen_links:
                continue
            seen_links.add(link)
            process_candidate(
                title=entry["title"],
                link=entry["link"],
                source_feed=entry.get("source_feed"),
                published_hint=entry.get("published_hint"),
                existing_url_hashes=existing_url_hashes,
                last_run_completed_at=last_run_completed_at,
            )

    state["last_run_completed_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    print("Done.")


if __name__ == "__main__":
    main()