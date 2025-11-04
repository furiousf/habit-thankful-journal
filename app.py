import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta

# --- Google Sheet setup ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(CREDS)

# Use your Google Sheet URL
sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/15hNZ96Lh5GGo0bQNl_XadE7B3Ii84XFBs7KH4Q03jLs/edit?usp=sharing"
).sheet1

# --- Page config ---
st.set_page_config(page_title="Habit Thankful Journal", page_icon="🪶", layout="centered")

# --- Sidebar navigation ---
st.sidebar.title("🪶 Habit Thankful Journal")
menu = st.sidebar.radio("Navigate", ["🏠 Home", "✍️ Create/Edit Today's Journal", "📖 Read Past Records"])

# --- Home Page ---
if menu == "🏠 Home":
    st.title("🪶 Habit Thankful Journal")
    st.write("Welcome to your gratitude space 🌿")
    st.markdown("""
    ### Choose an option from the sidebar:
    1️⃣ **Create/Edit Today's Journal** – write or update your reflections for today (or within the past 7 days).  
    2️⃣ **Read Past Records** – browse your previous gratitude entries stored in Google Sheets.  
    ---
    Take a moment each day to reflect on what you're thankful for 🌞
    """)

# --- Journal Entry Page ---
elif menu == "✍️ Create/Edit Today's Journal":
    st.title("✍️ Create or Edit Journal Entry")
    st.write("Take a moment to slow down and reflect ✨")

    today = date.today()
    min_date = today - timedelta(days=7)
    entry_date = st.date_input(
        "📅 Choose date (past 7 days only):",
        value=today,
        min_value=min_date,
        max_value=today
    )

    mood = st.selectbox("Mood", ["😊 Happy", "😐 Neutral", "😞 Sad", "🤩 Excited", "😔 Tired"])

    thank1_who = st.text_input("I thank (1):", placeholder="Who are you thankful for?")
    thank1_for = st.text_input("for (1):", placeholder="What did they do?")

    thank2_who = st.text_input("I thank (2):", placeholder="Who else?")
    thank2_for = st.text_input("for (2):", placeholder="What did they do?")

    thank3_who = st.text_input("I thank (3):", placeholder="Another person or thing?")
    thank3_for = st.text_input("for (3):", placeholder="What did they do?")

    thoughts = st.text_area("My thoughts and journey today...", height=200)

    if st.button("💾 Save to Google Sheet"):
        timestamp = f"{entry_date} {datetime.now().strftime('%H:%M')}"
        row = [
            timestamp,
            mood,
            thank1_who, thank1_for,
            thank2_who, thank2_for,
            thank3_who, thank3_for,
            thoughts
        ]
        sheet.append_row(row)
        st.success(f"✅ Entry saved for {entry_date}!")

# --- Read Records Page ---
elif menu == "📖 Read Past Records":
    st.title("📖 Read Past Journal Entries")

    records = sheet.get_all_records()
    if not records:
        st.info("No entries found yet 🌱")
    else:
        for r in records[::-1]:  # newest first
            st.markdown(f"""
            **📅 {r['timestamp']}** | {r['mood']}  
            🪶 1. I thank *{r['thank1_who']}* for *{r['thank1_for']}*  
            🪶 2. I thank *{r['thank2_who']}* for *{r['thank2_for']}*  
            🪶 3. I thank *{r['thank3_who']}* for *{r['thank3_for']}*  
            > {r['thoughts']}
            ---
            """)