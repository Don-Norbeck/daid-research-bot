# DAID Research Bot — Roadmap

> Local-first AI signal intelligence pipeline for DarkAIDefense.com

---

## v0.1 — Foundation (Released March 2026) ✅

End-to-end working pipeline. Local LLM analysis. Ranked signals. Pitch generation. Streamlit UI.

See [CHANGELOG.md](CHANGELOG.md) for full details.

---

## v0.2 — UI-First Editorial Workflow (In Progress)

The goal of v0.2 is to move the entire pipeline workflow into the UI and add an editorial feedback loop that improves signal quality over time.

### Feed Management
- [ ] Feed Manager tab in Streamlit — add, remove, enable/disable RSS feeds
- [ ] Save feed changes directly to `feeds.json` from the UI
- [ ] Curated feed suggestions organized by topic (governance, labor, misuse, power concentration)
- [ ] Feed health indicator — flag feeds returning errors or no new items

### Pipeline Runner
- [ ] "Run Capture", "Run Analysis", "Run Rank", "Run Pitch", "Run All" buttons in UI
- [ ] Progress indicator with status updates per stage
- [ ] Last run timestamp and item counts displayed in header
- [ ] One-click full pipeline from inside Streamlit — no terminal needed for normal operation

### Editorial Review
- [ ] Accept / Pass / Reclassify buttons on each pitch in the Article Ideas tab
- [ ] Accepted pitches saved to `data/editorial/accepted_YYYY-MM-DD.json`
- [ ] Reclassified signals (monitor → ignore) written back to suppression list
- [ ] Editorial log at `data/editorial/signal_memory.json` — builds your pattern over time

### Topic Configuration
- [ ] Editable topic list in the UI — add, remove, weight topics
- [ ] Saved to `config/topics.json`
- [ ] Topic config injected into `analyze_local.py` prompt at analysis time
- [ ] Per-topic signal counts shown in Trending tab

---

## v0.3 — Self-Learning Signal Intelligence

The goal of v0.3 is to make the system learn from editorial decisions and improve signal filtering automatically.

### Editorial Pattern Learning
- [ ] Analyzer reads `signal_memory.json` before each run
- [ ] Signals matching previously rejected patterns auto-scored lower
- [ ] Signals matching accepted patterns surfaced higher
- [ ] "Why suggested" explanation per pitch based on editorial history

### Thread Detection
- [ ] Cross-week signal clustering — connect related stories across multiple runs
- [ ] Thread view in UI: "This story is part of a 3-week pattern on agentic systems"
- [ ] Thread strength score — how many signals, how recent, which direction
- [ ] Thread-based article prompts: "You have enough material for a long-form piece on X"

### Source Intelligence
- [ ] Per-feed signal quality score — which feeds produce the most shortlisted signals
- [ ] Auto-suppress feeds that consistently produce only IGNORE decisions
- [ ] Source diversity check — flag when too many signals come from one feed

### Ignore Pattern Suppression
- [ ] After N weeks, topics that consistently score IGNORE auto-filtered before LLM analysis
- [ ] Configurable suppression threshold
- [ ] Manual override list — always analyze / never analyze

---

## v0.4 — Content Pipeline Integration

The goal of v0.4 is to connect the signal intelligence output directly to the DarkAIDefense writing workflow.

### Draft Generation
- [ ] "Start Draft" button on accepted pitches — generates a structured outline in your voice
- [ ] Draft includes: working title, lede seed, three section hooks, Gen X pattern reference, sources
- [ ] Output as `.md` file ready for Ulysses import

### LinkedIn Post Generator
- [ ] One-click LinkedIn post from any accepted signal
- [ ] Stays within single-screen format (your preference)
- [ ] Gen X register enforced — punchy, diagnostic, not preachy

### AI Risk Score Integration
- [ ] Accepted signals automatically contribute to running AI Risk Score
- [ ] Risk score dashboard in UI — current score, contributing signals, trend
- [ ] Export risk score report as structured Markdown

### Publishing Workflow
- [ ] Track article status: pitched → drafting → published
- [ ] Published articles linked back to source signals
- [ ] Coverage gap detector — topics with strong signals but no recent articles

---

## Backlog / Under Consideration

- Scheduled runs via Windows Task Scheduler integration
- Email digest of weekly pitch report
- Multi-model support — route different signal types to different local models
- OwnYourContext integration — memory portability for editorial preferences
- Export to Notion or Obsidian for long-form research notes

---

## Architecture Principles

- **Local-first** — all analysis runs on local hardware, no cloud LLM calls
- **Auditable** — every decision logged to JSONL with timestamps
- **Deterministic** — temperature=0, schema-enforced JSON output
- **Modular** — each pipeline stage is an independent script, replaceable
- **Editorial control** — the system surfaces signals, you make the call