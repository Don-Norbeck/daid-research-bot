import os
import json
import pandas as pd
import streamlit as st

# =========================
# CONFIG
# =========================

OUTPUT_DIR = "data/outputs"

st.set_page_config(
    page_title="DAID Signal Intelligence",
    layout="wide"
)

# =========================
# HELPERS
# =========================

def load_latest_file(prefix):
    if not os.path.exists(OUTPUT_DIR):
        return None

    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(prefix) and f.endswith(".json")]
    if not files:
        return None

    files.sort(
        key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
        reverse=True
    )

    path = os.path.join(OUTPUT_DIR, files[0])

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), path
    except Exception as e:
        st.error(f"Failed to load {path}: {e}")
        return None


def load_enriched_items_sorted(enriched_dir: str, limit: int = 25):
    if not os.path.exists(enriched_dir):
        return []

    items = []
    for filename in os.listdir(enriched_dir):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(enriched_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items.append(data)
        except Exception:
            continue

    items.sort(key=lambda x: x.get("analyzed_at", ""), reverse=True)
    return items[:limit]


# =========================
# LOAD DATA
# =========================

weekly_summary, summary_path = load_latest_file("weekly_summary_") or ([], "")
ranked_signals, ranked_path = load_latest_file("ranked_signals_") or ([], "")
top_signals, top_path = load_latest_file("top_signals_") or ([], "")

captured_count = len([
    f for f in os.listdir("data/items") if f.endswith(".json")
]) if os.path.exists("data/items") else 0

enriched_count = len([
    f for f in os.listdir("data/enriched") if f.endswith(".json")
]) if os.path.exists("data/enriched") else 0

output_count = len([
    f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")
]) if os.path.exists(OUTPUT_DIR) else 0


# =========================
# HEADER
# =========================

st.title("DAID Signal Intelligence Workbench")
st.caption("Local signal intelligence workbench for capture, analysis, ranking, and pitch generation.")

col1, col2, col3 = st.columns(3)
col1.metric("Captured Items", captured_count)
col2.metric("Enriched Items", enriched_count)
col3.metric("Output Files", output_count)


# =========================
# TABS
# =========================

tab1, tab2, tab3, tab4 = st.tabs([
    "Watchlist",
    "Pitch Bot",
    "Enriched Items",
    "Raw Outputs"
])


# =========================
# WATCHLIST TAB
# =========================

with tab1:
    st.header("Weekly Watchlist")

    if summary_path:
        st.caption(f"Loaded: {summary_path}")

    if not weekly_summary:
        st.warning("No weekly summary found. Run rank_signals.py to generate one.")
    else:
        df = pd.DataFrame(weekly_summary)

        if "url" in df.columns and "title" in df.columns:
            df["title"] = df.apply(
                lambda row: f"[{row['title']}]({row['url']})" if row.get("url") else row["title"],
                axis=1
            )

        st.dataframe(df, use_container_width=True)

        st.subheader("Top Signals")

        for item in weekly_summary:
            title = item.get("title", "Untitled")

            with st.expander(title):
                st.write(f"**Decision:** {item.get('decision')}")
                st.write(f"**Time Horizon:** {item.get('time_horizon')}")
                st.write(f"**Confidence:** {item.get('confidence')}")
                st.write(f"**Score:** {item.get('score')}")
                st.write(f"**Signal:** {item.get('signal')}")

                if item.get("url"):
                    st.markdown(f"[Read Article]({item['url']})")


# =========================
# PITCH BOT TAB
# =========================

with tab2:
    st.header("Pitch Bot")

    pitch_result = load_latest_file("pitch_ideas_") or load_latest_file("pitch_output_")
    pitch_file, pitch_path = pitch_result if pitch_result else (None, "")

    if pitch_path:
        st.caption(f"Loaded: {pitch_path}")

    if not pitch_file:
        st.info("Run pitch_bot.py to generate outputs.")
    else:
        if isinstance(pitch_file, dict):
            generated_at = pitch_file.get("generated_at", "")
            source_count = pitch_file.get("source_count", 0)
            if generated_at:
                st.caption(f"Generated: {generated_at} from {source_count} source signals")

            pitch_tabs = st.tabs(["Article Ideas", "LinkedIn Angles", "Risk Score Drivers"])

            # -------------------------
            # ARTICLE IDEAS
            # -------------------------
            with pitch_tabs[0]:
                for idea in pitch_file.get("article_ideas", []):
                    title = idea.get("title", "Untitled")
                    with st.expander(title):
                        col_a, col_b, col_c = st.columns(3)
                        col_a.write(f"**Theme:** {idea.get('theme', '—')}")
                        col_b.write(f"**Decision:** {idea.get('decision', '—')}")
                        col_c.write(f"**Score:** {idea.get('score', '—')}")

                        st.write(f"**Horizon:** {idea.get('time_horizon', '—')} · **Confidence:** {idea.get('confidence', '—')}")
                        st.write(f"**Signal:** {idea.get('primary_signal', '—')}")
                        st.write(f"**DAID Angle:** {idea.get('daid_angle', '—')}")
                        st.write(f"**Why it matters:** {idea.get('why_it_matters', '—')}")

                        hook = idea.get("controversy_hook", "")
                        if hook:
                            st.info(f"💡 {hook}")

                        pattern = idea.get("genx_pattern")
                        if pattern:
                            st.warning(
                                f"**Gen X lens — {pattern.get('pattern', '')}**\n\n"
                                f"_{pattern.get('reference', '')}_\n\n"
                                f"{pattern.get('frame', '')}"
                            )

                        if idea.get("url"):
                            st.markdown(f"[Source]({idea['url']})")

            # -------------------------
            # LINKEDIN ANGLES
            # -------------------------
            with pitch_tabs[1]:
                for angle in pitch_file.get("linkedin_angles", []):
                    label = angle.get("title", "Untitled")
                    with st.expander(label):
                        st.write(f"**Hook:** {angle.get('hook')}")
                        st.write(f"**Body Seed:** {angle.get('body_seed')}")
                        st.write(f"**CTA:** {angle.get('cta')}")
                        ref = angle.get("genx_reference")
                        if ref:
                            st.caption(f"Gen X reference: {ref}")
                        if angle.get("url"):
                            st.markdown(f"[Source]({angle['url']})")

            # -------------------------
            # RISK SCORE DRIVERS
            # -------------------------
            with pitch_tabs[2]:
                for driver in pitch_file.get("risk_score_candidates", []):
                    label = driver.get("title", "Untitled")
                    with st.expander(label):
                        st.write(f"**Theme:** {driver.get('theme')}")
                        st.write(f"**Suggested Risk Points:** {driver.get('suggested_risk_points')}")
                        st.write(f"**Rationale:** {driver.get('rationale')}")
                        if driver.get("url"):
                            st.markdown(f"[Source]({driver['url']})")

        else:
            # Fallback: flat list from older pitch_bot versions
            for idea in pitch_file:
                title = idea.get("title", "Untitled")
                with st.expander(title):
                    st.write(f"**Angle:** {idea.get('angle')}")
                    st.write(f"**Summary:** {idea.get('summary')}")
                    st.write(f"**Why it matters:** {idea.get('why_it_matters')}")
                    if idea.get("url"):
                        st.markdown(f"[Source]({idea['url']})")


# =========================
# ENRICHED ITEMS TAB
# =========================

with tab3:
    st.header("Enriched Items")

    enriched_dir = "data/enriched"
    enriched_items = load_enriched_items_sorted(enriched_dir, limit=25)

    if not enriched_items:
        st.warning("No enriched items found. Run analyze_local.py first.")
    else:
        st.caption(f"Showing {len(enriched_items)} most recently analyzed items")

        for data in enriched_items:
            title = data.get("title", data.get("doc_id", "Untitled"))
            analysis = data.get("analysis", {})
            decision = analysis.get("decision", "—")
            confidence = analysis.get("confidence", "—")

            label = f"[{decision.upper()}] {title}"

            with st.expander(label):
                col_a, col_b, col_c = st.columns(3)
                col_a.write(f"**Decision:** {decision}")
                col_b.write(f"**Confidence:** {confidence}")
                col_c.write(f"**Time Horizon:** {analysis.get('time_horizon', '—')}")

                st.write(f"**Published:** {data.get('published_at', '—')}")
                st.write(f"**Analyzed:** {data.get('analyzed_at', '—')}")

                if data.get("url"):
                    st.markdown(f"[Read Article]({data['url']})")

                st.write(f"**Primary Signal:** {analysis.get('primary_signal', '—')}")
                st.write(f"**DAID Angle:** {analysis.get('darkaidefense_angle', '—')}")
                st.write(f"**Why It Matters:** {analysis.get('why_it_matters', '—')}")

                hook = analysis.get("controversy_hook", "")
                if hook:
                    st.info(f"💡 {hook}")


# =========================
# RAW OUTPUTS TAB
# =========================

with tab4:
    st.header("Raw Outputs")

    if not os.path.exists(OUTPUT_DIR):
        st.warning("No outputs found.")
    else:
        files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")]
        files.sort(
            key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
            reverse=True
        )

        if not files:
            st.warning("No JSON output files found.")
        else:
            selected_file = st.selectbox("Select output file", files)

            if selected_file:
                path = os.path.join(OUTPUT_DIR, selected_file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    st.json(data)
                except Exception as e:
                    st.error(f"Error loading file: {e}")