import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# --- Google Sheet setup ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(CREDS)

# Use your Google Sheet URL (this is safest)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/15hNZ96Lh5GGo0bQNl_XadE7B3Ii84XFBs7KH4Q03jLs/edit?usp=sharing").sheet1

# --- Page layout ---
st.set_page_config(page_title="Habit Thankful Journal", page_icon="🪶", layout="centered")
st.title("🪶 Habit Thankful Journal")
st.write("Take a moment to slow down and reflect ✨")

# --- Date picker ---
entry_date = st.date_input("📅 Choose date:", value=date.today())

# --- Input form ---
mood = st.selectbox("Mood", ["😊 Happy", "😐 Neutral", "😞 Sad", "🤩 Excited", "😔 Tired"])

thank1_who = st.text_input("I thank (1):", placeholder="Who are you thankful for?")
thank1_for = st.text_input("for (1):", placeholder="What did they do?")

thank2_who = st.text_input("I thank (2):", placeholder="Who else?")
thank2_for = st.text_input("for (2):", placeholder="What did they do?")

thank3_who = st.text_input("I thank (3):", placeholder="Another person or thing?")
thank3_for = st.text_input("for (3):", placeholder="What did they do?")

thoughts = st.text_area("My thoughts and journey today...", height=200)

# --- Save to Google Sheet ---
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

# --- View recent entries ---
st.markdown("---")
st.subheader("📖 Recent Entries")

records = sheet.get_all_records()
if records:
    for r in records[-5:][::-1]:
        st.markdown(f"""
        **📅 {r['timestamp']}** | {r['mood']}  
        🪶 1. I thank *{r['thank1_who']}* for *{r['thank1_for']}*  
        🪶 2. I thank *{r['thank2_who']}* for *{r['thank2_for']}*  
        🪶 3. I thank *{r['thank3_who']}* for *{r['thank3_for']}*  
        > {r['thoughts']}
        ---
        """)
else:
    st.info("No entries yet. Start by writing your first gratitude today 🌱")