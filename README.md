# DAID Research Bot

> Local-first AI signal intelligence pipeline for [DarkAIDefense.com](https://darkaidefense.com)

**Current release:** v0.1 — Foundation  
**Status:** Working end-to-end pipeline  
**Next:** v0.2 — UI-first editorial workflow

---

## What this does

Turns raw RSS feeds into pitch-ready article ideas for DarkAIDefense.com.

```
RSS feeds → Capture → Analyze (local LLM) → Rank → Pitch → Streamlit UI
```

Each article is classified as IGNORE / MONITOR / SHORTLIST, scored, and surfaced with:
- A primary signal ("who did what and why it matters")
- A DAID governance/risk angle
- An optional controversy hook
- A Gen X pattern match (when the signal echoes a previous tech cycle)
- A Markdown pitch report ready for Ulysses

Everything runs locally. No cloud LLM calls. No data leaving your machine.

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Ollama and pull the model
```bash
# Install Ollama from https://ollama.com
ollama pull mistral-nemo:12b
```

### 3. Run the pipeline
```bash
python run_all.py
```

### 4. Launch the UI
```bash
python -m streamlit run app.py
```

### 5. Open your pitch report
```
data/outputs/pitch_report_YYYY-MM-DD.md
```

---

## Pipeline

| Script | Input | Output | Purpose |
|---|---|---|---|
| `capture_local.py` | `feeds.json` | `data/items/` | Ingest RSS feeds |
| `analyze_local.py` | `data/items/` | `data/enriched/` | LLM signal analysis |
| `rank_signals.py` | `data/enriched/` | `data/outputs/` | Score and rank signals |
| `pitch_bot.py` | `data/outputs/` | `data/outputs/` | Generate pitch content |
| `trending_tracker.py` | `data/outputs/` | `data/trends.json` | Track topic frequency |
| `app.py` | `data/outputs/` | Streamlit UI | Browse and review |
| `run_all.py` | — | — | Run full pipeline |

---

## Analyze flags

```bash
# Normal weekly run
python analyze_local.py

# Clear backlog (last 30 days, up to 200 items)
python analyze_local.py --days-back 30 --max 200

# Re-analyze after prompt update
python analyze_local.py --days-back 14 --max 100 --reanalyze
```

---

## Session Management (Windows)

```bash
start_ai_session.bat      # Clear GPU hogs, set Ollama env, launch pipeline
restore_session.bat       # Restart apps after pipeline completes
disable_startup_junk.bat  # One-time startup optimization (run as Administrator)
```

---

## Hardware Notes

Tested on Dell XPS 8700 with NVIDIA RTX 4060 (8GB VRAM).

- Close Teams, ChatGPT, LinkedIn, Steam before pipeline runs
- `mistral-nemo:12b` (7.1GB) requires ~4GB free VRAM
- `llama3.1:8b` (4.9GB) is the reliable fallback on constrained hardware
- Use `start_ai_session.bat` to automate VRAM clearing

---

## Project Files

```
daid-research-bot/
├── capture_local.py        # RSS ingestion
├── analyze_local.py        # LLM analysis
├── rank_signals.py         # Scoring and ranking
├── pitch_bot.py            # Pitch generation
├── trending_tracker.py     # Topic frequency tracking
├── app.py                  # Streamlit UI
├── run_all.py              # Pipeline orchestrator
├── feeds.json              # RSS feed list
├── prompts/
│   └── analyze_article.txt # LLM analysis prompt
├── data/
│   ├── items/              # Captured RSS items (gitignored)
│   ├── enriched/           # LLM-analyzed items (gitignored)
│   ├── outputs/            # Ranked signals + pitch reports (gitignored)
│   └── trends.json         # Topic frequency history (gitignored)
├── logs/                   # Audit logs (gitignored)
├── start_ai_session.bat    # Windows session manager
├── restore_session.bat     # Windows session restore
├── disable_startup_junk.bat # Windows startup optimizer
├── CHANGELOG.md
└── ROADMAP.md
```

---

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — release notes and what changed
- [ROADMAP.md](ROADMAP.md) — planned features for v0.2, v0.3, v0.4

---

## Built as part of

[DarkAIDefense.com](https://darkaidefense.com) — AI risk, governance, and societal impact.  
Author: Don Norbeck