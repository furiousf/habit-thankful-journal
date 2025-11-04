import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# --- Google Sheet setup ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(CREDS)

# Your Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/15hNZ96Lh5GGo0bQNl_XadE7B3Ii84XFBs7KH4Q03jLs/edit?usp=sharing"
sheet = client.open_by_url(SHEET_URL).sheet1

# --- Page setup ---
st.set_page_config(page_title="Habit Thankful Journal", page_icon="🪶", layout="centered")

# --- Session navigation ---
if "page" not in st.session_state:
    st.session_state.page = "home"

def goto(page):
    st.session_state.page = page
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# --- Load data ---
records = sheet.get_all_records()
df = pd.DataFrame(records) if records else pd.DataFrame(
    columns=["timestamp", "mood", "thank1_who", "thank1_for",
             "thank2_who", "thank2_for", "thank3_who", "thank3_for", "thoughts"]
)

# --- Helper ---
def get_thank_suggestions():
    names = pd.concat([
        df["thank1_who"], df["thank2_who"], df["thank3_who"]
    ]).dropna().unique().tolist()
    return sorted([n for n in names if n])

# --- HOME PAGE ---
if st.session_state.page == "home":
    st.title("🪶 Habit Thankful Journal")
    st.write("Welcome to your daily gratitude and reflection space 🌿")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✍️ Write / Edit Journal", use_container_width=True):
            goto("journal")
    with col2:
        if st.button("📊 Read & Stats", use_container_width=True):
            goto("stats")

    st.markdown("---")
    st.write("Reflect daily. Be thankful. Grow mindfully 🌞")

# --- JOURNAL PAGE ---
elif st.session_state.page == "journal":
    st.title("✍️ Create or Edit Journal Entry")

    today = date.today()
    min_date = today - timedelta(days=7)
    entry_date = st.date_input(
        "📅 Choose date (past 7 days only):",
        value=today,
        min_value=min_date,
        max_value=today
    )

    mood_list = ["😊 Happy", "😐 Neutral", "😞 Sad", "🤩 Excited", "😔 Tired"]

    df["date_only"] = df["timestamp"].apply(lambda x: str(x).split(" ")[0] if x else "")
    existing = df.loc[df["date_only"] == str(entry_date)]
    existing = existing.iloc[0].to_dict() if not existing.empty else {}

    thank_suggestions = get_thank_suggestions()

    mood = st.selectbox("Mood", mood_list,
                        index=mood_list.index(existing.get("mood", "😊 Happy")) if existing else 0)

    thank1_who = st.selectbox("I thank (1):", options=[""] + thank_suggestions,
                              index=([""] + thank_suggestions).index(existing.get("thank1_who", ""))
                              if existing.get("thank1_who", "") in thank_suggestions else 0)
    thank1_for = st.text_input("for (1):", value=existing.get("thank1_for", ""))

    thank2_who = st.selectbox("I thank (2):", options=[""] + thank_suggestions,
                              index=([""] + thank_suggestions).index(existing.get("thank2_who", ""))
                              if existing.get("thank2_who", "") in thank_suggestions else 0)
    thank2_for = st.text_input("for (2):", value=existing.get("thank2_for", ""))

    thank3_who = st.selectbox("I thank (3):", options=[""] + thank_suggestions,
                              index=([""] + thank_suggestions).index(existing.get("thank3_who", ""))
                              if existing.get("thank3_who", "") in thank_suggestions else 0)
    thank3_for = st.text_input("for (3):", value=existing.get("thank3_for", ""))

    thoughts = st.text_area("My thoughts and journey today...",
                            value=existing.get("thoughts", ""), height=200)

    if st.button("💾 Save to Google Sheet"):
        timestamp = f"{entry_date} {datetime.now().strftime('%H:%M')}"
        row_data = [
            timestamp, mood,
            thank1_who, thank1_for,
            thank2_who, thank2_for,
            thank3_who, thank3_for,
            thoughts
        ]
        if not existing:
            sheet.append_row(row_data)
            st.success(f"✅ New entry saved for {entry_date}!")
        else:
            row_index = df.index[df["date_only"] == str(entry_date)][0] + 2
            sheet.update(f"A{row_index}:I{row_index}", [row_data])
            st.success(f"✅ Updated entry for {entry_date}!")

    if st.button("🏠 Back to Home"):
        goto("home")

# --- STATS PAGE ---
elif st.session_state.page == "stats":
    st.title("📊 Mood & Gratitude Insights")

    if df.empty:
        st.info("No data yet 🌱 Please write some journal entries first.")
    else:
        # Convert timestamp to datetime
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # --- Quick filter buttons ---
        today = date.today()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Last 7 Days"):
                start_date = today - timedelta(days=7)
                end_date = today
            else:
                start_date = None
                end_date = None
        with col2:
            if st.button("Last 30 Days"):
                start_date = today - timedelta(days=30)
                end_date = today
        with col3:
            st.write("")  # filler

        # --- Manual date filter fallback ---
        if not start_date:
            default_start = date.today() - timedelta(days=30)
            date_range = st.date_input(
                "📅 Or select date range:",
                value=(default_start, date.today())
            )
            start_date, end_date = date_range

        # Filter
        mask = (df["timestamp_dt"].dt.date >= start_date) & (df["timestamp_dt"].dt.date <= end_date)
        filtered = df.loc[mask]

        # --- Chart type selector ---
        chart_type = st.radio("Chart type:", ["Bar", "Pie"], horizontal=True)

        # --- Mood chart ---
        st.subheader("😊 Mood trend")
        if not filtered.empty:
            mood_count = filtered.groupby("mood").size().reset_index(name="count")

            if chart_type == "Bar":
                st.bar_chart(mood_count.set_index("mood"))
            else:
                fig, ax = plt.subplots()
                ax.pie(mood_count["count"], labels=mood_count["mood"], autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No data for this period.")

        # --- People chart ---
        st.subheader("🙌 Most thanked people")
        people = pd.concat([
            filtered["thank1_who"], filtered["thank2_who"], filtered["thank3_who"]
        ]).dropna()
        if not people.empty:
            top_people = people.value_counts().head(10)
            if chart_type == "Bar":
                st.bar_chart(top_people)
            else:
                fig, ax = plt.subplots()
                ax.pie(top_people.values, labels=top_people.index, autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No people data for this period.")

    if st.button("🏠 Back to Home"):
        goto("home")