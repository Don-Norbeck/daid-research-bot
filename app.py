"""
app.py — DAID Signal Intelligence Workbench
v0.3: Pitch-bot-centric single page with reach-back accordions
"""

import json
import time
import subprocess
import threading
import queue
import requests
import streamlit as st
from datetime import datetime, timezone
from pathlib import Path

# =========================
# CONFIG
# =========================

OUTPUT_DIR    = Path("data/outputs")
ITEMS_DIR     = Path("data/items")
ENRICHED_DIR  = Path("data/enriched")
EDITORIAL_DIR = Path("data/editorial")
BRIEFS_DIR    = EDITORIAL_DIR / "briefs"
PROFILE_FILE  = Path("config/profile.json")
FEEDS_FILE    = Path("feeds.json")
CURATED_FILE  = Path("config/feeds_curated.json")
SETTINGS_FILE = Path("config/settings.json")
SIGNAL_MEMORY = EDITORIAL_DIR / "signal_memory.json"

OLLAMA_API_URL  = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

DEFAULT_ANALYSIS_MODEL     = "mistral-nemo:12b"
DEFAULT_CONVERSATION_MODEL = "llama3.1:latest"

PITCH_ARCHETYPES = {
    "The Straight Story":  "Write a direct, factual 250-word editorial brief. State what happened, why it matters for AI governance and risk, and the DAID angle. No spin. Signal-first, consequences second. Tone: analytical, grounded.",
    "The Connection":      "Write a 250-word editorial brief that connects two seemingly unrelated concepts or stories into a single through-line nobody else has drawn. Reveal the hidden pattern. Tone: curious, precise, slightly contrarian.",
    "The Cassandra":       "Write a 250-word editorial brief in full existential-stakes mode. What is the worst plausible outcome if this signal is ignored? Make the urgency felt without being hysterical. Gen X doom register. Tone: urgent, unflinching.",
    "The Comic Miss":      "Write a 250-word satirical editorial brief that deliberately misses the obvious point to make a deeper one. TPS report energy. The joke is the argument. Tone: dry, deadpan, Gen X office-culture humor.",
    "The Autopsy":         "Write a 250-word editorial brief treating this signal as post-mortem evidence. Something already failed — a policy, a promise, a product. What does the body tell us? Tone: forensic, matter-of-fact.",
    "The Pattern Match":   "Write a 250-word editorial brief using a Gen X cultural or historical echo. We have seen this exact playbook before — different decade, same move. Name the pattern, name the precedent, show the replay. Tone: knowing, slightly tired, precisely right.",
    "The Slow Burn":       "Write a 250-word editorial brief about why this signal is not urgent today but will be in 12-18 months. Make the case for paying attention now. Tone: measured, strategic, slightly ahead of the curve.",
}

ARCHETYPE_LIST = list(PITCH_ARCHETYPES.keys())

CURATED_FEEDS_DEFAULT = {
    "AI Governance & Policy": [
        {"name": "AI Now Institute",         "url": "https://ainowinstitute.org/category/news/feed"},
        {"name": "Future of Life Institute", "url": "https://futureoflife.org/feed/"},
        {"name": "CSET Georgetown",          "url": "https://cset.georgetown.edu/feed/"},
        {"name": "Stanford HAI",             "url": "https://hai.stanford.edu/news/rss.xml"},
        {"name": "Brookings Tech",           "url": "https://www.brookings.edu/topic/technology-innovation/feed/"},
    ],
    "Agentic Systems & Automation": [
        {"name": "LangChain Blog",           "url": "https://blog.langchain.dev/rss/"},
        {"name": "Interconnects.ai",         "url": "https://www.interconnects.ai/feed"},
        {"name": "The Gradient",             "url": "https://www.thegradient.pub/rss/"},
        {"name": "Hugging Face Blog",        "url": "https://huggingface.co/blog/feed.xml"},
        {"name": "Replicate Blog",           "url": "https://replicate.com/blog/rss"},
    ],
    "Labor & Economic Disruption": [
        {"name": "MIT Technology Review",    "url": "https://www.technologyreview.com/feed/"},
        {"name": "One Useful Thing",         "url": "https://www.oneusefulthing.org/feed"},
        {"name": "VentureBeat AI",           "url": "https://venturebeat.com/category/ai/feed/"},
        {"name": "The Register AI",          "url": "https://www.theregister.com/software/ai_ml/headlines.atom"},
    ],
    "AI Misuse & Security": [
        {"name": "Wired AI",                 "url": "https://www.wired.com/feed/tag/ai/latest/rss"},
        {"name": "AI News",                  "url": "https://www.artificialintelligence-news.com/feed/rss/"},
        {"name": "TechCrunch AI",            "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
        {"name": "The Verge AI",             "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    ],
    "Infrastructure & Power Concentration": [
        {"name": "SemiAnalysis",             "url": "https://www.semianalysis.com/feed"},
        {"name": "NVIDIA Developer Blog",    "url": "https://developer.nvidia.com/blog/feed"},
        {"name": "IEEE Spectrum AI",         "url": "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss"},
        {"name": "MIT News ML",              "url": "https://news.mit.edu/topic/mitmachine-learning-rss.xml"},
    ],
    "Scientific Acceleration": [
        {"name": "DeepMind Blog",            "url": "https://deepmind.com/blog/feed/basic/"},
        {"name": "OpenAI Blog",              "url": "https://openai.com/blog/rss/"},
        {"name": "Cohere Blog",              "url": "https://txt.cohere.ai/rss/"},
    ],
    "Culture & Media Criticism": [
        {"name": "Last Week in AI",          "url": "https://lastweekin.ai/feed"},
        {"name": "Reuters Tech",             "url": "https://www.reutersagency.com/feed/?best-topics=tech"},
    ],
}

DEFAULT_TOPICS = [
    "AI governance & policy",
    "Agentic systems & automation risk",
    "Labor & economic disruption",
    "AI misuse & security",
    "Infrastructure & power concentration",
    "Scientific acceleration",
    "Gen X culture & media criticism",
    "AI equity & bias",
]

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="DAID Signal Intelligence",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .pitch-brief {
        background: #1a1a2e;
        border-left: 3px solid #e94560;
        padding: 1.4rem 1.6rem;
        border-radius: 4px;
        margin: 1rem 0;
        line-height: 1.7;
    }
    .status-ok  { color: #00d26a; font-weight: 600; }
    .status-err { color: #e94560; font-weight: 600; }
    .rss-warn {
        background: #2a1a0e; border-left: 3px solid #f7b731;
        padding: 0.6rem 1rem; border-radius: 4px; margin-bottom: 0.8rem;
    }
    .rss-ok {
        background: #0e2a1a; border-left: 3px solid #00d26a;
        padding: 0.6rem 1rem; border-radius: 4px; margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================

def ensure_dirs():
    for d in [OUTPUT_DIR, ITEMS_DIR, ENRICHED_DIR, EDITORIAL_DIR, BRIEFS_DIR,
              Path("config"), Path("logs")]:
        d.mkdir(parents=True, exist_ok=True)

ensure_dirs()


def load_json(path: Path, default=None):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default if default is not None else {}


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_feeds():
    return load_json(FEEDS_FILE, default=[])


def save_feeds(feeds):
    save_json(FEEDS_FILE, feeds)


def load_profile():
    return load_json(PROFILE_FILE, default={})


def save_profile(p):
    save_json(PROFILE_FILE, p)


def load_settings():
    return load_json(SETTINGS_FILE, default={
        "analysis_model": DEFAULT_ANALYSIS_MODEL,
        "conv_model":     DEFAULT_CONVERSATION_MODEL,
        "days_back":      7,
        "max_items":      100,
    })


def save_settings(s):
    save_json(SETTINGS_FILE, s)


def load_signal_memory():
    return load_json(SIGNAL_MEMORY, default={"accepted": [], "passed": []})


def save_signal_memory(m):
    save_json(SIGNAL_MEMORY, m)


def load_latest_file(prefix: str):
    if not OUTPUT_DIR.exists():
        return None, ""
    files = sorted(
        [f for f in OUTPUT_DIR.iterdir() if f.name.startswith(prefix) and f.name.endswith(".json")],
        key=lambda f: f.stat().st_mtime, reverse=True
    )
    if not files:
        return None, ""
    try:
        return load_json(files[0]), str(files[0])
    except Exception:
        return None, ""


def count_files(path: Path, ext=".json") -> int:
    if not path.exists():
        return 0
    return sum(1 for f in path.iterdir() if f.suffix == ext)


def rss_age_days() -> float:
    state = load_json(Path("data/state.json"), default={})
    last = state.get("last_run_completed_at")
    if not last:
        return 999.0
    try:
        dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    except Exception:
        return 999.0


def ollama_is_running() -> bool:
    try:
        return requests.get(OLLAMA_TAGS_URL, timeout=3).status_code == 200
    except Exception:
        return False


def get_available_models() -> list:
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def model_label(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["starcoder", "codellama", "deepseek-coder"]):
        return f"{name}  ⚠️ Code model — not for conversation"
    if "code" in n and not any(x in n for x in ["llama", "mistral", "hermes"]):
        return f"{name}  ⚠️ Code model — not for conversation"
    if any(x in n for x in ["embed", "nomic", "bge"]):
        return f"{name}  ⚠️ Embedding model — not for generation"
    if any(x in n for x in ["70b", "72b", "65b", "34b"]):
        return f"{name}  — Too large for most local hardware"
    if any(x in n for x in ["13b", "14b", "15b"]):
        return f"{name}  — Large · Slow · Thorough"
    if any(x in n for x in ["7b", "8b", "9b", "11b", "12b"]):
        return f"{name}  — Medium · Balanced"
    if any(x in n for x in ["3b", "2b", "1b", "mini", "small", "phi", "tiny"]):
        return f"{name}  — Small · Fast · Brief"
    return f"{name}  — Unknown size"


def ollama_chat(model: str, messages: list) -> str:
    try:
        r = requests.post(OLLAMA_CHAT_URL,
                          json={"model": model, "messages": messages, "stream": False},
                          timeout=60)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "").strip()
    except Exception:
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        return ollama_generate(model, prompt)


def ollama_generate(model: str, prompt: str, timeout: int = 120) -> str:
    try:
        r = requests.post(OLLAMA_API_URL,
                          json={"model": model, "prompt": prompt,
                                "stream": False, "options": {"temperature": 0.7}},
                          timeout=timeout)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
        return f"[Error: {e}]"


def run_pipeline_step(cmd: list, log_queue: queue.Queue):
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=Path(__file__).parent,
        )
        for line in proc.stdout:
            log_queue.put(line.rstrip())
        proc.wait()
        log_queue.put(f"__EXIT__{proc.returncode}")
    except Exception as e:
        log_queue.put(f"[ERROR] {e}")
        log_queue.put("__EXIT__1")


def run_steps_in_sequence(steps: dict, log_queue: queue.Queue):
    for label, cmd in steps.items():
        log_queue.put(f"\n=== {label} ===")
        inner_q = queue.Queue()
        t = threading.Thread(target=run_pipeline_step, args=(cmd, inner_q), daemon=True)
        t.start()
        while True:
            try:
                line = inner_q.get(timeout=0.5)
                if line.startswith("__EXIT__"):
                    code = line.replace("__EXIT__", "")
                    if code != "0":
                        log_queue.put(f"❌ {label} failed — stopping.")
                        log_queue.put("__EXIT__1")
                        return
                    log_queue.put(f"✅ {label} complete.")
                    break
                log_queue.put(line)
            except queue.Empty:
                continue
    log_queue.put("__EXIT__0")


def stream_log(log_q: queue.Queue, placeholder, max_lines: int = 50) -> str:
    log_lines = list(st.session_state.get("pipeline_log", []))
    exit_code = "0"
    while True:
        try:
            line = log_q.get(timeout=0.3)
            if line.startswith("__EXIT__"):
                exit_code = line.replace("__EXIT__", "")
                break
            log_lines.append(line)
            placeholder.code("\n".join(log_lines[-max_lines:]), language=None)
        except queue.Empty:
            placeholder.code("\n".join(log_lines[-max_lines:]), language=None)
    st.session_state.pipeline_log = log_lines
    return exit_code


# =========================
# SESSION STATE INIT
# =========================

for key, val in [
    ("pipeline_log", []),
    ("pipeline_running", False),
    ("current_brief", None),
    ("current_archetype_idx", 0),
    ("interests_chat", [{
        "role": "assistant",
        "content": "What do you want to write about? It doesn't have to be AI-specific."
    }]),
]:
    if key not in st.session_state:
        st.session_state[key] = val

if "suggested_topics" not in st.session_state:
    st.session_state.suggested_topics = load_profile().get("suggested_topics", [])

# =========================
# LOAD CORE DATA
# =========================

settings       = load_settings()
profile        = load_profile()
running        = ollama_is_running()
age_days       = rss_age_days()
weekly_summary, summary_path = load_latest_file("weekly_summary_")
signal_memory  = load_signal_memory()
accepted_urls  = {s.get("url") for s in signal_memory.get("accepted", [])}
analysis_model = settings.get("analysis_model", DEFAULT_ANALYSIS_MODEL)

# =========================
# HEADER BAR
# =========================

hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([2, 1, 1, 1, 1, 2])
hc1.markdown("## 🛡 DAID Signal Intelligence")
hc2.metric("Captured",  count_files(ITEMS_DIR))
hc3.metric("Enriched",  count_files(ENRICHED_DIR))
hc4.metric("Feeds",     len(load_feeds()))
hc5.metric("Ollama",    "✓ Running" if running else "✗ Offline")

if age_days < 3:
    hc6.success(f"RSS: {age_days:.0f}d ago ✓")
elif age_days < 7:
    hc6.warning(f"RSS: {age_days:.0f}d ago")
else:
    hc6.error(f"RSS: {age_days:.0f}d ago — refresh?")

st.divider()

# =========================
# PITCH BOT — MAIN AREA
# =========================

st.header("✍️ Pitch Bot")

if not weekly_summary:
    st.warning("No signals yet. Open **Want fresher stories?** below and run the pipeline.")
else:
    # Signal selector — accepted float to top, then shortlisted
    def signal_sort_key(s):
        if s.get("url", "") in accepted_urls:
            return 0
        if s.get("decision") == "shortlist":
            return 1
        return 2

    sorted_signals = sorted(weekly_summary, key=signal_sort_key)

    def signal_display(s):
        prefix = "✅ " if s.get("url", "") in accepted_urls else ""
        icon   = "🟢" if s.get("decision") == "shortlist" else "🔵"
        return f"{icon} {prefix}{s.get('title', 'Untitled')}"

    # Controls row
    pc1, pc2, pc3 = st.columns([4, 2, 1])

    with pc1:
        selected_idx = st.selectbox(
            "Signal", options=range(len(sorted_signals)),
            format_func=lambda i: signal_display(sorted_signals[i]),
            key="pitch_signal_select", label_visibility="collapsed"
        )
        selected_signal = sorted_signals[selected_idx]

    with pc2:
        selected_archetype = st.selectbox(
            "Archetype", options=ARCHETYPE_LIST,
            index=st.session_state.current_archetype_idx,
            key="pitch_archetype_select", label_visibility="collapsed"
        )

    with pc3:
        if st.button("🎲 Next angle", key="next_arch",
                     help="Rotate to next archetype"):
            st.session_state.current_archetype_idx = (
                st.session_state.current_archetype_idx + 1
            ) % len(ARCHETYPE_LIST)
            st.session_state.current_brief = None
            st.rerun()

    # Signal detail (collapsed)
    with st.expander("Signal details", expanded=False):
        st.write(f"**{selected_signal.get('decision','—').upper()}** · "
                 f"Score: {selected_signal.get('score', 0):.4f} · "
                 f"{selected_signal.get('time_horizon', '—')}")
        st.write(f"**Signal:** {selected_signal.get('signal', '—')}")
        st.write(f"**DAID Angle:** {selected_signal.get('darkaidefense_angle', '—')}")
        hook = selected_signal.get("controversy_hook", "")
        if hook:
            st.info(f"💡 {hook}")
        if selected_signal.get("url"):
            st.markdown(f"[Source ↗]({selected_signal['url']})")

    st.caption(f"**{selected_archetype}** — {PITCH_ARCHETYPES[selected_archetype][:110]}...")

    # Feedback + action row
    fb_col, gen_col, remix_col = st.columns([4, 1, 1])
    with fb_col:
        feedback = st.text_input(
            "Steer",
            placeholder="e.g. 'add the labor angle', 'make it angrier', 'Philadelphia focus'...",
            key="pitch_feedback", label_visibility="collapsed"
        )
    with gen_col:
        generate_btn = st.button("⚡ Generate", type="primary", key="generate_pitch")
    with remix_col:
        remix_btn = st.button("🔄 Remix", key="remix_pitch",
                              help="Same signal + archetype, different wording",
                              disabled=st.session_state.current_brief is None)

    # Generate
    if generate_btn or remix_btn:
        if not running:
            st.error("Ollama is offline — start it in Advanced Settings below.")
        else:
            voice_note   = profile.get("voice", "")
            urgency_note = profile.get("urgency_bias", "")
            topics_note  = ", ".join(profile.get("topics", profile.get("default_topics", [])))
            remix_note   = "\nThis is a REMIX — reword significantly, find a different entry point." \
                           if remix_btn else ""

            prompt = f"""You are a senior editor at DarkAIDefense.com, an AI risk and governance publication with a Gen X voice.

SIGNAL:
Title: {selected_signal.get('title', '')}
Primary Signal: {selected_signal.get('signal') or selected_signal.get('primary_signal', '')}
DAID Angle: {selected_signal.get('darkaidefense_angle', '')}
Why It Matters: {selected_signal.get('why_it_matters', '')}
Controversy Hook: {selected_signal.get('controversy_hook', '')}
Source: {selected_signal.get('url', '')}

AUTHOR CONTEXT:
Voice: {voice_note}
Temperature: {urgency_note}
Topics of interest: {topics_note}

ARCHETYPE: {selected_archetype}
{PITCH_ARCHETYPES[selected_archetype]}
{f'FEEDBACK: {feedback}' if feedback.strip() else ''}
{remix_note}

Write EXACTLY a 250-word editorial brief.
Format:
**Headline:** one punchy line
**Brief:** 250 words
**The Angle:** one sentence
**Suggested lede:** one sentence

Output only the brief. No preamble."""

            with st.spinner(f"Generating {selected_archetype}..."):
                result = ollama_generate(analysis_model, prompt, timeout=120)

            st.session_state.current_brief = {
                "signal_title": selected_signal.get("title", ""),
                "signal_url":   selected_signal.get("url", ""),
                "archetype":    selected_archetype,
                "brief":        result,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "feedback":     feedback,
                "model":        analysis_model,
            }
            st.rerun()

    # Brief display
    if st.session_state.current_brief:
        bd = st.session_state.current_brief
        st.markdown(
            f'<div class="pitch-brief">'
            f'{bd["brief"].replace(chr(10), "<br>")}'
            f'</div>',
            unsafe_allow_html=True
        )

        ac1, ac2, ac3, ac4 = st.columns(4)

        with ac1:
            sig_url = selected_signal.get("url", "")
            if sig_url and sig_url not in accepted_urls:
                if st.button("✅ Accept signal", key="accept_signal"):
                    signal_memory["accepted"].append({
                        "url":        sig_url,
                        "title":      selected_signal.get("title", ""),
                        "decided_at": datetime.now(timezone.utc).isoformat()
                    })
                    save_signal_memory(signal_memory)
                    st.rerun()
            else:
                st.caption("✅ Accepted")

        with ac2:
            if st.button("📋 Copy", key="copy_brief"):
                st.code(bd["brief"], language=None)

        with ac3:
            if st.button("💾 Save brief", key="save_brief"):
                BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
                save_json(BRIEFS_DIR / f"brief_{ts}.json", bd)
                st.success("Saved.")

        with ac4:
            st.caption(f"`{bd.get('model', '—')}`")

        # Saved briefs history
        saved_briefs = sorted(BRIEFS_DIR.glob("*.json"),
                              key=lambda p: p.stat().st_mtime, reverse=True)
        if saved_briefs:
            with st.expander(f"Saved briefs ({len(saved_briefs)})", expanded=False):
                for bp in saved_briefs[:10]:
                    bdata = load_json(bp, default={})
                    label = f"{bdata.get('archetype', '—')} — {bdata.get('signal_title', '')[:55]}"
                    with st.expander(label):
                        st.caption(f"{bdata.get('generated_at', '')[:16]}  ·  {bdata.get('model', '')}")
                        st.markdown(bdata.get("brief", ""))
                        if bdata.get("signal_url"):
                            st.markdown(f"[Source ↗]({bdata['signal_url']})")

# =========================
# REACH-BACK ACCORDIONS
# =========================

st.divider()
st.caption("Need something different? Expand any section below.")

# ----------------------------------------------------------------
# 1. WANT FRESHER STORIES?
# ----------------------------------------------------------------

age_label = f"{age_days:.0f} days ago" if age_days < 999 else "never run"
with st.expander(f"📡 Want fresher stories?  —  Last RSS pull: {age_label}",
                 expanded=(age_days >= 7)):

    if age_days >= 7:
        st.markdown(
            f'<div class="rss-warn">⚠️ It\'s been <strong>{age_days:.0f} days</strong> '
            f'since the last feed pull.</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="rss-ok">✓ Feeds pulled {age_days:.1f} days ago.</div>',
            unsafe_allow_html=True
        )

    st.caption(f"{len(load_feeds())} feeds configured  ·  {count_files(ITEMS_DIR)} items captured")

    r1, r2 = st.columns(2)
    with r1:
        if st.button("📡 Pull RSS feeds now",
                     type="primary" if age_days >= 7 else "secondary",
                     disabled=st.session_state.pipeline_running,
                     key="rss_pull"):
            st.session_state.pipeline_log = []
            st.session_state.pipeline_running = True
            log_q = queue.Queue()
            threading.Thread(
                target=run_pipeline_step,
                args=(["python", "capture_local.py"], log_q), daemon=True
            ).start()
            ph = st.empty()
            code = stream_log(log_q, ph)
            st.session_state.pipeline_running = False
            if code == "0":
                st.success("Feeds pulled. Run Analysis → Pitch to update signals.")
            else:
                st.error("Feed pull failed — check log above.")
            st.rerun()

    with r2:
        if st.button("⚡ Pull + Re-analyze + Pitch",
                     disabled=st.session_state.pipeline_running,
                     key="rss_full"):
            steps = {
                "Capture RSS":      ["python", "capture_local.py"],
                "Analyze Items":    ["python", "analyze_local.py",
                                     "--days-back", str(int(settings.get("days_back", 7))),
                                     "--max",       str(int(settings.get("max_items", 100)))],
                "Rank Signals":     ["python", "rank_signals.py"],
                "Generate Pitches": ["python", "pitch_bot.py"],
            }
            st.session_state.pipeline_log = []
            st.session_state.pipeline_running = True
            log_q = queue.Queue()
            threading.Thread(
                target=run_steps_in_sequence, args=(steps, log_q), daemon=True
            ).start()
            ph = st.empty()
            code = stream_log(log_q, ph)
            st.session_state.pipeline_running = False
            if code == "0":
                st.success("Done — pitches updated.")
            st.rerun()

# ----------------------------------------------------------------
# 2. WANT DIFFERENT TOPICS?
# ----------------------------------------------------------------

active_topics = profile.get("topics", profile.get("default_topics", []))
topics_summary = ", ".join(active_topics[:4]) + ("..." if len(active_topics) > 4 else "") \
    if active_topics else "none set"

with st.expander(f"🎯 Want different topics?  —  {topics_summary}", expanded=False):

    t_left, t_right = st.columns([1, 1], gap="large")

    with t_left:
        updated_profile = dict(profile)
        current_default = profile.get("default_topics", [])
        selected_defaults = []
        st.markdown("**Check what applies:**")
        dcols = st.columns(2)
        for i, topic in enumerate(DEFAULT_TOPICS):
            if dcols[i % 2].checkbox(topic, value=(topic in current_default), key=f"dt_{i}"):
                selected_defaults.append(topic)
        updated_profile["default_topics"] = selected_defaults

        if st.session_state.suggested_topics:
            st.markdown("**Suggested from conversation:**")
            current_sug = profile.get("suggested_topics_selected", [])
            selected_sug = []
            scols = st.columns(2)
            for i, topic in enumerate(st.session_state.suggested_topics):
                if scols[i % 2].checkbox(topic, value=(topic in current_sug), key=f"st_{i}"):
                    selected_sug.append(topic)
            updated_profile["suggested_topics_selected"] = selected_sug
            updated_profile["suggested_topics"] = st.session_state.suggested_topics

        all_topics = list(dict.fromkeys(
            selected_defaults + updated_profile.get("suggested_topics_selected", [])
        ))
        updated_profile["topics"] = all_topics

        st.divider()
        voice_opts = [
            "Analytical — signal first, argument second",
            "Provocateur — challenge assumptions, create friction",
            "Diagnostician — find what's broken and name it",
            "Generational — Gen X lens, pattern recognition",
            "Policy wonk — frameworks, accountability, governance",
        ]
        cv = profile.get("voice", voice_opts[0])
        updated_profile["voice"] = st.radio(
            "Voice", voice_opts,
            index=voice_opts.index(cv) if cv in voice_opts else 0,
            key="interests_voice"
        )
        temp_opts = [
            "Measured — let the signal speak",
            "Urgent — the stakes are higher than people realize",
            "Skeptical — most AI hype is noise",
            "Historical — we've seen this before",
        ]
        ct = profile.get("urgency_bias", temp_opts[0])
        updated_profile["urgency_bias"] = st.radio(
            "Temperature", temp_opts,
            index=temp_opts.index(ct) if ct in temp_opts else 0,
            key="interests_temp"
        )

        tb1, tb2 = st.columns(2)
        with tb1:
            if st.button("💾 Save topics", key="save_topics"):
                updated_profile["saved_at"] = datetime.now(timezone.utc).isoformat()
                save_profile(updated_profile)
                st.success(f"Saved — {len(all_topics)} topics.")
                st.rerun()
        with tb2:
            if st.button("⚡ Save + Re-analyze + Pitch",
                         disabled=st.session_state.pipeline_running,
                         key="topics_rerun"):
                updated_profile["saved_at"] = datetime.now(timezone.utc).isoformat()
                save_profile(updated_profile)
                steps = {
                    "Analyze Items":    ["python", "analyze_local.py",
                                         "--days-back", str(int(settings.get("days_back", 7))),
                                         "--max",       str(int(settings.get("max_items", 100)))],
                    "Rank Signals":     ["python", "rank_signals.py"],
                    "Generate Pitches": ["python", "pitch_bot.py"],
                }
                st.session_state.pipeline_log = []
                st.session_state.pipeline_running = True
                log_q = queue.Queue()
                threading.Thread(
                    target=run_steps_in_sequence, args=(steps, log_q), daemon=True
                ).start()
                ph = st.empty()
                code = stream_log(log_q, ph)
                st.session_state.pipeline_running = False
                if code == "0":
                    st.success("Done — pitches updated with new topics.")
                st.rerun()

    with t_right:
        st.caption("Talk through what you want to cover — AI will suggest topics.")
        running_now = ollama_is_running()
        if not running_now:
            st.warning("Ollama offline — start it in Advanced Settings.")
        else:
            models = get_available_models()
            CODE_SIG = ["code", "starcoder", "embed", "nomic", "stable", "whisper"]
            chat_cands = [m for m in models if not any(s in m.lower() for s in CODE_SIG)]
            conv_model = settings.get("conv_model", DEFAULT_CONVERSATION_MODEL)
            if conv_model not in chat_cands:
                conv_model = chat_cands[0] if chat_cands else (models[0] if models else DEFAULT_CONVERSATION_MODEL)
            st.caption(f"Using: `{conv_model}`")

        chat_box = st.container(height=260)
        with chat_box:
            for msg in st.session_state.interests_chat:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        user_in = st.chat_input("What should DAID be covering...", key="interests_chat_input")
        if user_in:
            st.session_state.interests_chat.append({"role": "user", "content": user_in})
            if running_now:
                sys_p = ("You are an editorial strategy assistant. "
                         "Topics can be anything — AI, labor, culture, policy, economics, society. "
                         "Be direct. Ask one follow-up question at a time.")
                response = ollama_chat(conv_model,
                    [{"role": "system", "content": sys_p}] + st.session_state.interests_chat)
                full_convo = "\n".join(
                    f"{m['role']}: {m['content']}" for m in st.session_state.interests_chat
                )
                raw = ollama_generate(conv_model,
                    f"Based on this conversation, suggest 6-8 broad editorial topics. "
                    f"Return ONLY a JSON array of short strings.\n\n{full_convo}", timeout=30)
                try:
                    clean = raw.strip().strip("```json").strip("```").strip()
                    suggestions = json.loads(clean)
                    if isinstance(suggestions, list):
                        merged = list(dict.fromkeys(
                            st.session_state.suggested_topics + [str(s) for s in suggestions]
                        ))
                        st.session_state.suggested_topics = merged[:16]
                except Exception:
                    pass
            else:
                response = "Ollama is offline."
            st.session_state.interests_chat.append({"role": "assistant", "content": response})
            st.rerun()

# ----------------------------------------------------------------
# 3. CHANGE YOUR FEEDS?
# ----------------------------------------------------------------

feeds = load_feeds()
with st.expander(f"📻 Change your feeds?  —  {len(feeds)} active", expanded=False):

    f_left, f_right = st.columns([1, 1], gap="large")

    with f_left:
        st.markdown("**Active feeds**")
        to_remove = []
        for i, url in enumerate(feeds):
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            fc1, fc2 = st.columns([5, 1])
            fc1.markdown(f"`{domain}`")
            if fc2.button("✕", key=f"rm_{i}"):
                to_remove.append(url)
        if to_remove:
            save_feeds([f for f in feeds if f not in to_remove])
            st.rerun()

        st.markdown("**Add a feed**")
        new_url = st.text_input("", placeholder="https://example.com/feed.xml",
                                key="new_feed_url", label_visibility="collapsed")
        if st.button("＋ Add", key="add_feed"):
            if new_url and new_url not in feeds:
                feeds.append(new_url.strip())
                save_feeds(feeds)
                st.success("Added.")
                st.rerun()
            elif new_url in feeds:
                st.warning("Already in list.")

    with f_right:
        st.markdown("**Curated library**")
        curated = load_json(CURATED_FILE, default=None) or CURATED_FEEDS_DEFAULT
        if not CURATED_FILE.exists():
            save_json(CURATED_FILE, CURATED_FEEDS_DEFAULT)
        current_urls = set(feeds)
        for category, cfeed_list in curated.items():
            with st.expander(f"{category} ({len(cfeed_list)})"):
                for feed in cfeed_list:
                    cc1, cc2 = st.columns([4, 1])
                    cc1.markdown(f"**{feed['name']}**")
                    if feed["url"] in current_urls:
                        cc2.markdown("✓")
                    else:
                        if cc2.button("＋", key=f"cf_{feed['url']}"):
                            feeds.append(feed["url"])
                            save_feeds(feeds)
                            st.rerun()

# ----------------------------------------------------------------
# 4. WANT A DIFFERENT VOICE?
# ----------------------------------------------------------------

with st.expander(f"🤖 Want a different voice?  —  Using: {analysis_model}", expanded=False):

    if not running:
        st.warning("Ollama is offline.")
        if st.button("▶ Start Ollama", key="start_ollama_v"):
            try:
                subprocess.Popen(["ollama", "serve"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(str(e))
    else:
        available_models = get_available_models()
        if available_models:
            CODE_SIG   = ["code", "starcoder", "embed", "nomic", "stable", "whisper"]
            conv_only  = [m for m in available_models if not any(s in m.lower() for s in CODE_SIG)]
            ana_idx    = available_models.index(settings["analysis_model"]) \
                         if settings["analysis_model"] in available_models else 0
            conv_idx   = conv_only.index(settings["conv_model"]) \
                         if settings["conv_model"] in conv_only else 0

            v1, v2 = st.columns(2)
            with v1:
                new_ana = st.selectbox(
                    "Analysis model (pitch generation)",
                    options=available_models, format_func=model_label,
                    index=ana_idx, key="voice_ana"
                )
            with v2:
                new_conv = st.selectbox(
                    "Conversation model (topics chat)",
                    options=conv_only if conv_only else available_models,
                    format_func=model_label,
                    index=conv_idx, key="voice_conv"
                )

            if new_ana != settings["analysis_model"] or new_conv != settings["conv_model"]:
                settings["analysis_model"] = new_ana
                settings["conv_model"]     = new_conv
                save_settings(settings)
                analysis_model = new_ana

            vc1, vc2 = st.columns(2)
            with vc1:
                if st.button("⚡ Load model into memory", key="load_model_v"):
                    with st.spinner(f"Loading {new_ana}..."):
                        res = ollama_generate(new_ana, "Ready.", timeout=60)
                        if res.startswith("[Error"):
                            st.error(res)
                        else:
                            st.success(f"{new_ana} ready.")
            with vc2:
                if st.button("🔄 Regenerate brief with this model",
                             key="regen_model_v",
                             disabled=st.session_state.current_brief is None):
                    st.session_state.current_brief = None
                    st.rerun()
        else:
            st.warning("No models found. Run: `ollama pull mistral-nemo:12b`")

# ----------------------------------------------------------------
# 5. ADVANCED SETTINGS
# ----------------------------------------------------------------

with st.expander("⚙️ Advanced settings", expanded=False):

    adv1, adv2 = st.columns(2)

    with adv1:
        st.markdown("**Pipeline settings**")
        new_days = st.number_input(
            "Analysis window (days back)", min_value=1, max_value=90,
            value=int(settings.get("days_back", 7)), key="adv_days"
        )
        new_max = st.number_input(
            "Max items per analysis run", min_value=10, max_value=500,
            value=int(settings.get("max_items", 100)), key="adv_max"
        )
        if st.button("💾 Save settings", key="save_adv"):
            settings["days_back"] = new_days
            settings["max_items"] = new_max
            save_settings(settings)
            st.success("Saved.")

        st.markdown("**Ollama**")
        if not running:
            if st.button("▶ Start Ollama", key="start_ollama_adv", type="primary"):
                try:
                    subprocess.Popen(["ollama", "serve"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.success("Ollama is running.")
        if st.button("🔄 Refresh status", key="refresh_adv"):
            st.rerun()

    with adv2:
        st.markdown("**Run individual pipeline steps**")
        STEPS = {
            "Capture RSS":      ["python", "capture_local.py"],
            "Analyze Items":    ["python", "analyze_local.py",
                                 "--days-back", str(int(settings.get("days_back", 7))),
                                 "--max",       str(int(settings.get("max_items", 100)))],
            "Rank Signals":     ["python", "rank_signals.py"],
            "Generate Pitches": ["python", "pitch_bot.py"],
        }
        for label, cmd in STEPS.items():
            if st.button(f"▶ {label}", key=f"adv_{label}",
                         disabled=st.session_state.pipeline_running):
                st.session_state.pipeline_running = True
                log_q = queue.Queue()
                threading.Thread(
                    target=run_pipeline_step, args=(cmd, log_q), daemon=True
                ).start()
                ph = st.empty()
                code = stream_log(log_q, ph)
                st.session_state.pipeline_running = False
                st.caption("✅ Complete" if code == "0" else f"❌ Failed (exit {code})")
                st.rerun()

    if st.session_state.pipeline_log:
        st.divider()
        st.caption("Last run log")
        st.code("\n".join(st.session_state.pipeline_log[-40:]), language=None)