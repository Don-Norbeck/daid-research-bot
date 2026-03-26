# DAID Research Bot — Changelog

---

## v0.2 — Pitch-Bot-Centric UI
**Released:** March 26, 2026

Complete redesign of the Streamlit interface. Replaced the five-tab layout with a single-page, pitch-bot-centric experience. The Pitch Bot is now the home screen — everything else is subordinate, accessible through reach-back accordions only when needed.

### What changed

**UI architecture — full rewrite of `app.py`**

The tab-based layout (System / Interests / Feeds / Signals / Pitch Bot) was replaced with a single scrolling page organized around the editorial workflow:

- **Pitch Bot** is the dominant view — signal selector, archetype picker, feedback field, Generate and Remix buttons, brief output, and saved briefs history
- **Five reach-back accordions** below the brief, closed by default, labeled by intent rather than function:
  - 📡 Want fresher stories? — RSS age status, Pull Feeds, Pull + Re-analyze + Pitch
  - 🎯 Want different topics? — topic editor, AI conversation for suggestions, Save + Re-analyze + Pitch
  - 📻 Change your feeds? — active feed list with remove, add by URL, curated library
  - 🤖 Want a different voice? — model selector with size/speed labels, load into memory, regenerate brief
  - ⚙️ Advanced settings — pipeline settings, individual step buttons, Ollama controls

**Pitch Bot**
- Seven named archetypes: The Straight Story, The Connection, The Cassandra, The Comic Miss, The Autopsy, The Pattern Match, The Slow Burn
- Each archetype has a distinct system prompt shaping the 250-word brief
- **Next Angle** button rotates archetypes without losing signal selection
- **Remix** button regenerates the same signal + archetype with fresh wording
- **Feedback field** steers the brief — freetext injected into the generation prompt
- Author voice and editorial temperature from profile injected into every brief
- Active topics from interests profile included in context
- Accept signal button writes to `data/editorial/signal_memory.json`
- Copy, Save brief, and saved briefs history with expander view
- Model shown in corner of brief output

**RSS age indicator**
- Header bar shows days since last feed pull
- Green under 3 days, yellow 3-7 days, red over 7 days
- "Want fresher stories?" accordion auto-expands when feeds are over 7 days old

**Model management**
- Model dropdowns now use labeled options showing size and speed: `mistral-nemo:12b — Medium · Balanced`
- Code and embedding models flagged with ⚠️ warnings in dropdowns
- Models too large for typical local hardware labeled accordingly
- Model selections auto-save to `config/settings.json` on change — no Save button needed
- "Load analysis model into memory" button warms up the selected analysis model

**Topics / Interests**
- Default topic checklist (8 AI-focused topics) as a baseline
- AI conversation in the same panel surfaces additional topic suggestions dynamically
- Suggested topics appear as a second checkbox list — select what applies
- Both lists merge into `profile["topics"]` on save
- Save + Re-analyze + Pitch runs the analysis pipeline immediately after saving

**Feed manager**
- Active feed list with per-feed remove buttons
- Add by URL with duplicate detection
- Curated feed library organized by topic category (7 categories, ~35 feeds)
- One-click add from curated library

**Pipeline runner**
- Split into two logical operations: **Refresh Feeds** (capture only) and **Run Analysis → Pitch** (analyze + rank + pitch, no capture)
- Individual stage buttons available in Advanced Settings for debugging
- Live log streaming for all pipeline operations
- `config/settings.json` stores days-back window and max items, passed to `analyze_local.py` as flags

**Signal memory**
- Accept / Pass decisions written to `data/editorial/signal_memory.json`
- Accepted signals float to the top of the Pitch Bot signal selector

### Hardware notes
Tested on Dell XPS 8700 with NVIDIA RTX 3060 (12GB VRAM).
Brief generation: 10-15 seconds on `mistral-nemo:12b` with model warm in memory.
Close GPU-heavy background apps before pipeline runs.

### Known limitations
- Topics set in Interests must be saved before they influence analysis — not yet injected into `analyze_local.py` prompt automatically
- Signal memory stores accept/pass decisions but does not yet influence ranking scores
- Feed health indicators (error detection per feed) deferred to v0.3
- `st.text_input("")` empty label warnings in terminal — cosmetic only, no functional impact

---

## v0.1 — Foundation
**Released:** March 18, 2026

First working end-to-end release. Local LLM signal intelligence pipeline for DarkAIDefense.com content research.

### What it does
Captures RSS feeds → analyzes each article with a local LLM → filters and ranks signals → generates pitch-ready content → surfaces everything in a Streamlit workbench.

### Pipeline
```
capture_local.py    →  ingest RSS feeds         →  data/items/
analyze_local.py    →  LLM analysis             →  data/enriched/
rank_signals.py     →  scoring + ranking         →  data/outputs/
pitch_bot.py        →  pitch generation          →  data/outputs/
trending_tracker.py →  topic frequency tracking  →  data/trends.json
app.py              →  Streamlit UI
run_all.py          →  one-command pipeline runner
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
- Gen X Pattern Library — 10 cultural patterns matched against signal text
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
- Enriched Items tab — sorted by analyzed_at descending, decision badge in label
- Raw Outputs tab — file selector sorted by most recent

### Requirements
```
Python 3.12+
Ollama (local)
mistral-nemo:12b or llama3.1:8b (fallback for constrained VRAM)
streamlit>=1.35.0
pandas>=2.2.0
requests>=2.31.0
```

### Hardware notes
Tested on Dell XPS 8700 with NVIDIA RTX 3060 (12GB VRAM).
Close GPU-heavy background apps before pipeline runs.
`llama3.1:8b` is the reliable fallback if `mistral-nemo:12b` fails to load due to VRAM pressure.