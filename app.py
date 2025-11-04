import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# --- Page setup ---
st.set_page_config(
    page_title="Habit Thankful Journal",
    page_icon="🪶",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- STATS PAGE ---
elif st.session_state.page == "stats":
    st.title("📊 Mood & Gratitude Insights")

    if df.empty:
        st.info("No data yet 🌱 Please write some journal entries first.")
    else:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
        today = date.today()

        # --- Quick filters ---
        col1, col2, col3 = st.columns([1, 1, 2])
        selected_filter = st.session_state.get("selected_filter", None)

        with col1:
            if st.button("Last 7 Days"):
                st.session_state.selected_filter = "7"
        with col2:
            if st.button("Last 30 Days"):
                st.session_state.selected_filter = "30"

        # --- Date range handling ---
        if st.session_state.get("selected_filter") == "7":
            start_date = today - timedelta(days=7)
            end_date = today
            st.info(f"📅 Showing data from **{start_date}** to **{end_date}** (Last 7 days)")
        elif st.session_state.get("selected_filter") == "30":
            start_date = today - timedelta(days=30)
            end_date = today
            st.info(f"📅 Showing data from **{start_date}** to **{end_date}** (Last 30 days)")
        else:
            default_start = today - timedelta(days=30)
            date_range = st.date_input(
                "📅 Select date range:",
                value=(default_start, today)
            )
            start_date, end_date = date_range
            st.info(f"📅 Showing data from **{start_date}** to **{end_date}**")

        # --- Filter data ---
        mask = (df["timestamp_dt"].dt.date >= start_date) & (df["timestamp_dt"].dt.date <= end_date)
        filtered = df.loc[mask]

        # --- Chart type toggle ---
        chart_type = st.radio("Chart type:", ["Bar", "Pie"], horizontal=True)

        # --- Mood chart ---
        st.subheader("😊 Mood distribution")
        if not filtered.empty:
            mood_count = filtered.groupby("mood").size().reset_index(name="count")

            if chart_type == "Bar":
                st.bar_chart(mood_count.set_index("mood"), height=200)
            else:
                fig, ax = plt.subplots(figsize=(3, 3))
                ax.pie(mood_count["count"], labels=mood_count["mood"],
                       autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No mood data for this period.")

        # --- People chart ---
        st.subheader("🙌 Most thanked people")
        people = pd.concat([
            filtered["thank1_who"], filtered["thank2_who"], filtered["thank3_who"]
        ]).dropna()
        if not people.empty:
            top_people = people.value_counts().head(10)
            if chart_type == "Bar":
                st.bar_chart(top_people, height=200)
            else:
                fig, ax = plt.subplots(figsize=(3, 3))
                ax.pie(top_people.values, labels=top_people.index,
                       autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No people data for this period.")

    if st.button("🏠 Back to Home"):
        goto("home")