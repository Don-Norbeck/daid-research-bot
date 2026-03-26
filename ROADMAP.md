# DAID Research Bot — Roadmap

> Local-first AI signal intelligence pipeline for DarkAIDefense.com

---

## v0.1 — Foundation (Released March 18, 2026) ✅

End-to-end working pipeline. Local LLM analysis. Ranked signals. Pitch generation. Streamlit UI.

See [CHANGELOG.md](CHANGELOG.md) for full details.

---

## v0.2 — Pitch-Bot-Centric UI (Released March 26, 2026) ✅

Single-page pitch-bot-centric experience replacing the five-tab layout. Pitch Bot is the home screen. Five reach-back accordions for fresher stories, different topics, feed changes, model swaps, and advanced settings. Seven named archetypes. Remix, Next Angle, and feedback-steered generation. RSS age indicator. Model size/speed labels. Signal accept/pass memory.

See [CHANGELOG.md](CHANGELOG.md) for full details.

---

## v0.3 — Signal Learning & Editorial Memory

The goal of v0.3 is to make the system learn from your editorial decisions and surface better signals over time. Accept/pass decisions already write to `signal_memory.json` — this version makes those decisions count.

### Editorial Pattern Learning
- [ ] `rank_signals.py` reads `signal_memory.json` before scoring — accepted signal patterns score higher, passed patterns score lower
- [ ] "Why suggested" explanation per signal in the Pitch Bot — e.g. "Similar to 3 articles you accepted on agentic systems"
- [ ] Signals from previously passed sources auto-deprioritized (not suppressed — just ranked lower)
- [ ] Accepted signal themes surface as topic suggestions in the Interests accordion

### Thread Detection
- [ ] Cross-week signal clustering — connect related stories across multiple runs
- [ ] Thread indicator in signal selector: "Part of a 3-week pattern on agentic systems"
- [ ] Thread strength score — how many signals, how recent, which direction
- [ ] Thread-based prompt: "You have enough material for a long-form piece on X"

### Feed Intelligence
- [ ] Per-feed signal quality score — which feeds produce the most shortlisted signals
- [ ] Feed health indicator — flag feeds returning errors or no new items
- [ ] Auto-deprioritize feeds that consistently produce only IGNORE decisions (configurable threshold)
- [ ] Source diversity check — flag when too many signals come from one feed

### Interests → Analysis Integration
- [ ] Topics saved in Interests injected into `analyze_local.py` prompt at analysis time — not just used for pitch context
- [ ] Keyword weighting: topics you've selected score higher in the ranking formula
- [ ] Per-topic signal counts visible in the topics accordion

---

## v0.4 — Article Draft & Memory

The goal of v0.4 is to take the 250-word brief all the way to a publishable draft, and to remember what you've published so the system can surface connections and gaps.

### Draft Generation
- [ ] "Expand to full article" button in Pitch Bot — takes the brief and generates a full 800-1200 word draft
- [ ] Editable draft area in the UI — edit inline before saving
- [ ] Draft rendered as Markdown compatible with Ulysses — `##`/`###` headings, bold, no HTML
- [ ] Energy usage figure at close (watt-hours + 100W bulb equivalent) — auto-appended
- [ ] Copy full draft button
- [ ] Model selector per draft — local Ollama vs Claude API

### Article Memory Store
- [ ] Local JSON store — one record per saved draft, written on save
- [ ] Bot infers metadata: slug, date, title, tags, summary, key citations, related topics
- [ ] `memory/articles/` folder, gitignored by default
- [ ] Saved articles viewable in a "Published" accordion on the main page

### Coverage Intelligence
- [ ] Update detection — new signal matches topic covered in prior article, surfaces the prior piece
- [ ] Coverage gap detector — topics with strong signals but no published article
- [ ] "You've written about this before" prompt when selecting a signal with prior coverage

---

## v0.5 — Knowledge Graph & Distribution

The goal of v0.5 is to make the full body of work queryable and to close the loop from draft to published to distributed.

### Knowledge Graph
- [ ] Link graph built from shared topics across articles
- [ ] Explicit thread connections — Claww → OpenClaw → follow-up pieces
- [ ] Visual graph view: node = article, edge = shared topic or thread link
- [ ] Filter by topic, date range, archetype used

### Social Distribution
- [ ] LinkedIn single-screen post generator from brief or full article
- [ ] Bluesky thread adapter
- [ ] Post history stored alongside article memory

### Scheduling & Automation
- [ ] Scheduled RSS capture via Windows Task Scheduler integration
- [ ] Weekly email digest of pitch report
- [ ] "Run Analysis → Pitch" on a schedule — new signals waiting when you open the app

---

## Backlog / Under Consideration

- RSS feed discovery by topic — find feeds from a description, not a known URL
- Multi-publication mode — run separate pitch pipelines for different audiences or outlets
- OwnYourContext integration — editorial preferences portable across AI systems
- Export to Notion or Obsidian for long-form research notes
- Mac setup and packaging guide
- `st.text_input("")` empty label warnings — fix for accessibility compliance

---

## Architecture Principles

- **Local-first** — all analysis runs on local hardware, no cloud LLM calls by default
- **Pitch-bot-centric** — the brief is the product; everything else supports getting there
- **Auditable** — every pipeline decision logged to JSONL with timestamps
- **Deterministic** — temperature=0, schema-enforced JSON output for analysis
- **Editorial control** — the system surfaces signals and generates briefs; you make every call
- **Modular** — each pipeline stage is an independent script, replaceable
- **No schema setup** — structure inferred from content, not configured by hand
- **Portable** — voice profiles, topics, and article memory travel with the user