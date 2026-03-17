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
    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(prefix)]
    if not files:
        return None

    files.sort(reverse=True)
    path = os.path.join(OUTPUT_DIR, files[0])

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path


# =========================
# LOAD DATA
# =========================

weekly_summary, summary_path = load_latest_file("weekly_summary_") or ([], "")
ranked_signals, ranked_path = load_latest_file("ranked_signals_") or ([], "")
top_signals, top_path = load_latest_file("top_signals_") or ([], "")

captured_count = len(os.listdir("data/items")) if os.path.exists("data/items") else 0
enriched_count = len(os.listdir("data/enriched")) if os.path.exists("data/enriched") else 0
output_count = len(os.listdir(OUTPUT_DIR)) if os.path.exists(OUTPUT_DIR) else 0


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
        st.warning("No weekly summary found.")
    else:
        df = pd.DataFrame(weekly_summary)

        # Make titles clickable
        if "url" in df.columns:
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

    pitch_file, pitch_path = load_latest_file("pitch_output_") or ([], "")

    if pitch_path:
        st.caption(f"Loaded: {pitch_path}")

    if not pitch_file:
        st.info("Run pitch_bot.py to generate outputs.")
    else:
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

    if not os.path.exists(enriched_dir):
        st.warning("No enriched items found.")
    else:
        files = os.listdir(enriched_dir)

        for filename in files[:25]:  # limit for performance
            path = os.path.join(enriched_dir, filename)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                title = data.get("title", filename)

                with st.expander(title):
                    st.write(f"**URL:** {data.get('url')}")
                    st.write(f"**Published:** {data.get('published_at')}")
                    st.write(f"**Analysis:** {data.get('analysis')}")

            except Exception as e:
                st.error(f"Error loading {filename}: {e}")


# =========================
# RAW OUTPUTS TAB
# =========================

with tab4:
    st.header("Raw Outputs")

    if not os.path.exists(OUTPUT_DIR):
        st.warning("No outputs found.")
    else:
        files = os.listdir(OUTPUT_DIR)

        selected_file = st.selectbox("Select output file", files)

        if selected_file:
            path = os.path.join(OUTPUT_DIR, selected_file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                st.json(data)

            except Exception as e:
                st.error(f"Error loading file: {e}")