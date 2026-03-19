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
- [ ] Editorial log at `data/editorial/signal_memory.json` — builds pattern over time

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

## v0.4 — Editorial Workspace

The goal of v0.4 is a full editorial workspace between the ranked signal list and the published article. The pipeline surfaces signals — the workspace is where you turn them into content.

### Voice Alignment System
- [ ] Nine-position alignment selector: Framing axis (Concrete / Neutral / Conceptual) × Temperature axis (Measured / Neutral / Charged)
- [ ] Named alignment personas: The Analyst, The Reporter, The Correspondent, The Observer, The Signal (Auto), The Provocateur, The Strategist, The Theorist, The Evangelist
- [ ] Per-alignment prompt fragment injected at draft time
- [ ] Usage counter per alignment — tracks picks over time, surfaces default suggestion
- [ ] Named voice profiles — save, load, edit combinations
- [ ] Repitch with different alignment without changing global settings

### Modifier Stack
- [ ] Toggle modifiers stacked on top of active alignment: analogy density, jargon level, cultural reference temperature, plain language, explain it to grandma, zero em-dash, passive voice off, lead with data / story / provocation
- [ ] Custom modifier field — describe in 3 words or less, feeds directly into prompt
- [ ] Up to 5 custom modifier slots per profile
- [ ] Modifier combinations saveable as part of named voice profile

### Pitch Angle vs Article Voice — Separated
- [ ] Pitch bot angle settings: what lens to apply when surfacing and framing signals
- [ ] Article draft voice settings: how the piece is written
- [ ] Angle set at pitch time, voice confirmed or adjusted at draft time

### Editorial Workspace UI
- [ ] Editable prompt field pre-populated from pitch output — edit before draft fires
- [ ] Model selector: local Ollama vs Claude API, selectable per draft
- [ ] Draft renders as scrollable Markdown in app
- [ ] Redraft button preserving prompt edits
- [ ] Citation request controls — request, review, edit inline citations
- [ ] Copy button — full Markdown block, Ulysses-optimized
- [ ] Save button — writes approved article to memory store, metadata inferred by bot

### Canonical Article Output
- [ ] Single Markdown-compatible plain text block
- [ ] `##` / `###` headings, bold formatting, no HTML or WordPress tags
- [ ] Inline citation links as standard Markdown `[text](url)`
- [ ] Energy usage figure at close (watt-hours + 100W bulb equivalent)
- [ ] Ready to paste into Ulysses and publish without reformatting

---

## v0.5 — Article Memory and Knowledge Graph

The goal of v0.5 is to make the body of published work queryable — surfacing connections between articles, detecting when new signals update prior coverage, and enabling topic curation and mind mapping across the full archive.

### Article Memory Store
- [ ] Local JSON store — one record per published article, written on save
- [ ] Bot infers metadata from content: slug, date, title, tags, summary, key citations, related topics
- [ ] No manual schema setup — structure extracted automatically at save time
- [ ] `memory/articles/` folder inside repo, gitignored by default

### Knowledge Graph
- [ ] Link graph built from inferred related[] across articles
- [ ] Explicit thread connections: Claww → OpenClaw → follow-up pieces
- [ ] Update detection — new signal matches topic covered in prior article, surfaces the prior piece
- [ ] Coverage gap detector — topics with strong signals but no published article

### Topic Curation
- [ ] Bundle articles by tag or theme into curated collections
- [ ] Collection view in UI — "all DAID articles on agentic systems"
- [ ] Export curated collection as linked Markdown index

### Mind Map View
- [ ] Visual graph of article relationships in UI
- [ ] Node = article, edge = shared topic or explicit thread link
- [ ] Click node to open article record
- [ ] Filter by topic, date range, alignment used

---

## Backlog / Under Consideration

- RSS feed discovery via topic — find feeds from a topic description, not a known URL
- Multi-topic configuration — run separate pitch pipelines for different publications or audiences
- Social post adapters — LinkedIn single-screen post, Bluesky thread, from canonical article object
- Scheduled runs via Windows Task Scheduler integration
- Email digest of weekly pitch report
- OwnYourContext integration — memory portability for editorial preferences
- Export to Notion or Obsidian for long-form research notes
- Mac setup guide (deferred from v0.1)

---

## Architecture Principles

- **Local-first** — all analysis runs on local hardware, no cloud LLM calls by default
- **Auditable** — every decision logged to JSONL with timestamps
- **Deterministic** — temperature=0, schema-enforced JSON output
- **Modular** — each pipeline stage is an independent script, replaceable
- **Editorial control** — the system surfaces signals, you make the call
- **No schema setup** — structure inferred from content, not configured by hand
- **Portable** — voice profiles and article memory travel with the user