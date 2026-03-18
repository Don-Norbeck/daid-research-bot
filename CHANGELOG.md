# DAID Research Bot — Changelog

---

## v0.1 — Foundation
**Released:** March 18, 2026

First working end-to-end release. Local LLM signal intelligence pipeline for DarkAIDefense.com content research.

### What it does
Captures RSS feeds → analyzes each article with a local LLM → filters and ranks signals → generates pitch-ready content → surfaces everything in a Streamlit workbench.

### Pipeline
```
capture_local.py   →  ingest RSS feeds          →  data/items/
analyze_local.py   →  LLM analysis              →  data/enriched/
rank_signals.py    →  scoring + ranking          →  data/outputs/
pitch_bot.py       →  pitch generation           →  data/outputs/
trending_tracker.py → topic frequency tracking  →  data/trends.json
app.py             →  Streamlit UI
run_all.py         →  one-command pipeline runner
```

### Features

**Capture (`capture_local.py`)**
- RSS + Atom feed ingestion across 23 curated AI/tech feeds
- URL deduplication via SHA-256 hash — no duplicate captures across runs
- robots.txt compliance
- Topic keyword tagging at capture time
- Incremental capture — only processes new items since last run
- State tracking via `data/state.json`

**Analysis (`analyze_local.py`)**
- Local LLM via Ollama (default: `mistral-nemo:12b`)
- Structured JSON output enforced via schema at temperature=0
- Signal classification: IGNORE / MONITOR / SHORTLIST
- Time horizon tagging: immediate / near_term / long_term / archival
- Confidence scoring with enforced variance (no defaulting to 0.7)
- Optional `controversy_hook` field — one-line provocation when signal has cultural resonance
- Candidate items sorted newest-first before analysis
- `--days-back N` flag for targeted backlog clearing
- `--max N` flag to control items per run (default: 100)
- `--reanalyze` flag to re-process existing enriched files after prompt updates
- Retry logic with 2 attempts per item
- Full JSONL audit log at `logs/analyze_local.jsonl`

**Ranking (`rank_signals.py`)**
- URL-based deduplication across enriched files — same story on multiple days counts once
- Timezone-aware date comparison (fixes silent weekly window bug)
- Scoring formula: `decision_weight × time_weight × confidence`
- Weekly window filter (default: 7 days)
- Outputs: `ranked_signals_*.json`, `top_signals_*.json`, `weekly_summary_*.json`
- Full analysis fields preserved in weekly summary (darkaidefense_angle, why_it_matters, controversy_hook)

**Pitch Generation (`pitch_bot.py`)**
- Gen X Pattern Library — 10 cultural patterns matched against signal text without additional LLM calls:
  - The Pink Slip Pattern (labor displacement)
  - The Governance Lag (policy always arrives late)
  - The Wind-Up Toy Problem (autonomous system drift)
  - The Platform Lock-In Cycle (infrastructure as strategy)
  - The Data Bargain (free products and their real cost)
  - The Dual-Use Default (capability misuse)
  - The Balloon Animal Economy (valuation vs reality)
  - The TPS Report Problem (performative productivity)
  - The Science Acceleration Gap (capability outpacing ethics)
  - The Creative Class Squeeze (platform disruption of creative work)
- Theme classification across 8 signal categories
- Outputs Markdown pitch report (`pitch_report_*.md`) formatted for Ulysses
- Outputs structured JSON for UI (`pitch_ideas_*.json`)
- Shortlisted signals get full treatment; monitor signals condensed

**Trending Tracker (`trending_tracker.py`)**
- Persists topic frequency week-over-week to `data/trends.json`
- Tracks last 12 weeks
- Rising / stable / fading / new trend indicators
- Injected into weekly Markdown report header

**Streamlit UI (`app.py`)**
- Watchlist tab — ranked signals with clickable titles, score, horizon, confidence
- Pitch Bot tab — Article Ideas (with Gen X lens + controversy hook), LinkedIn Angles, Risk Score Drivers
- Enriched Items tab — sorted by analyzed_at descending, decision badge in label, controversy hook inline
- Raw Outputs tab — file selector sorted by most recent

**Session Management**
- `start_ai_session.bat` — kills GPU/RAM hogs, sets Ollama env vars, launches pipeline
- `restore_session.bat` — restarts killed apps after pipeline completes
- `disable_startup_junk.bat` — one-time startup optimization (run as Administrator)

### LLM Prompt (`prompts/analyze_article.txt`)
- Selective classification with enforced distribution (most = IGNORE)
- Confidence variance rules — no defaulting
- Signal extraction format: "Who did what, and why it matters"
- DAID contextualization step
- Time horizon classification
- Optional controversy_hook generation with quality bar (weak hooks return "")

### Known Limitations
- `data/items/` backlog: 1,445 captured items, 200 analyzed as of v0.1
- No UI controls for pipeline execution — scripts run from terminal
- Feed management requires manual editing of `feeds.json`
- Editorial feedback not yet implemented — no way to mark pitches as accepted/rejected
- Trending data requires 3-4 weekly runs before trend directions are meaningful

### Requirements
```
Python 3.12+
Ollama (local)
mistral-nemo:12b or llama3.1:8b (fallback for constrained VRAM)
streamlit>=1.35.0
pandas>=2.2.0
requests>=2.31.0
```

### Hardware Notes
Tested on Dell XPS 8700 with NVIDIA RTX 4060 (8GB VRAM).
Close GPU-heavy background apps before pipeline runs (Teams, ChatGPT, LinkedIn, Steam).
Use `start_ai_session.bat` to automate this.
`llama3.1:8b` is the reliable fallback if `mistral-nemo:12b` fails to load due to VRAM pressure.

---

## v0.2 — UI-First Editorial Workflow
**Status:** In development

See [ROADMAP.md](ROADMAP.md) for planned features.