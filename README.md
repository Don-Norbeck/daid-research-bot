# DAID Signal Intelligence

A local AI-powered signal intelligence pipeline for tracking AI risk, governance, and societal impact.

Built as part of DarkAIDefense.

---

## What this does

This system turns raw RSS feeds into:

- Structured AI risk signals
- Ranked weekly intelligence
- Pitch-ready article ideas
- AI Risk Score drivers

Pipeline:

RSS → Capture → Analyze (LLM) → Rank → Pitch → UI

---

## Key Features

- Local LLM analysis (Ollama)
- Signal extraction (not summarization)
- Risk-focused classification (IGNORE / MONITOR / SHORTLIST)
- Time horizon tagging
- Confidence scoring
- Weekly ranking engine
- Pitch generation (articles, LinkedIn, risk drivers)
- Streamlit UI

---

## Why this exists

Most AI tools summarize content.

This system is designed to answer:

**"What actually matters?"**

With a focus on:

- AI risk
- governance
- misuse
- labor disruption
- power concentration

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt